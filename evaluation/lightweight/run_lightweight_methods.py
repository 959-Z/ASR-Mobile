#!/usr/bin/env python3
"""
Small-scale lightweight ASR experiments for ASR-Mobile.

The script runs a GPU-first pipeline:
  1. baseline Whisper tiny evaluation
  2. base -> tiny pseudo-label distillation
  3. magnitude pruning at selected sparsity levels
  4. pruning recovery fine-tuning
  5. CSV, Markdown report, and plots

It intentionally uses the existing short benchmark audio so the experiment is
reproducible and does not require downloading a large speech dataset.
"""

from __future__ import annotations

import argparse
import csv
import gc
import json
import os
import re
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = PROJECT_ROOT.parent / ".cache"
os.environ.setdefault("HF_HOME", str(CACHE_ROOT / "huggingface"))
os.environ.setdefault("HF_DATASETS_CACHE", str(CACHE_ROOT / "huggingface" / "datasets"))
os.environ.setdefault("TRANSFORMERS_CACHE", str(CACHE_ROOT / "huggingface" / "transformers"))
os.environ.setdefault("TORCH_HOME", str(CACHE_ROOT / "torch"))
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import soundfile as sf
import torch
import torch.nn.utils.prune as prune
from jiwer import cer, wer
from torch.optim import AdamW
from tqdm import tqdm
from transformers import WhisperForConditionalGeneration, WhisperProcessor


@dataclass
class Sample:
    lang: str
    lang_name: str
    label: str
    expected: str
    audio_path: Path


TEST_PHRASES = [
    ("en", "English", "Greeting", "How are you doing today"),
    ("en", "English", "Weather", "The weather is very nice outside"),
    ("en", "English", "Order", "I would like a cup of coffee"),
    ("zh", "Chinese", "Greeting_zh", "你好今天天气怎么样"),
    ("zh", "Chinese", "Order_zh", "我想订一杯咖啡"),
    ("zh", "Chinese", "Thanks", "谢谢你的帮助"),
    ("fr", "French", "Salutation", "Bonjour comment allez vous"),
    ("fr", "French", "Commande", "Je voudrais un cafe"),
    ("fr", "French", "Thanks_fr", "Merci pour votre aide"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--teacher", default="openai/whisper-base")
    parser.add_argument("--student", default="openai/whisper-tiny")
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "lightweight_experiments" / "results"))
    parser.add_argument("--sample-limit", type=int, default=0, help="0 means use all local samples")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--max-train-steps", type=int, default=9)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--prune-amounts", nargs="+", type=float, default=[0.10, 0.20, 0.30])
    parser.add_argument("--recovery-prune-amount", type=float, default=0.20)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--smoke", action="store_true", help="Use 3 samples and 3 training steps")
    parser.add_argument("--skip-distill", action="store_true")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def load_samples(sample_limit: int = 0) -> List[Sample]:
    audio_dir = PROJECT_ROOT / "evaluation" / "pc_benchmark" / "test_audio"
    samples: List[Sample] = []
    for lang, lang_name, label, expected in TEST_PHRASES:
        path = audio_dir / f"{lang}_{label}.wav"
        if path.exists():
            samples.append(Sample(lang, lang_name, label, expected, path))
    if sample_limit and sample_limit > 0:
        return samples[:sample_limit]
    return samples


def load_audio(path: Path) -> np.ndarray:
    audio, sr = sf.read(str(path))
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    if sr != 16000:
        import librosa

        audio = librosa.resample(audio.astype(np.float32), orig_sr=sr, target_sr=16000)
    return audio.astype(np.float32)


def normalize_text(text: str, lang: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    if lang == "zh":
        return re.sub(r"[^\w\u4e00-\u9fff]", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def score_text(reference: str, prediction: str, lang: str) -> float:
    ref = normalize_text(reference, lang)
    hyp = normalize_text(prediction, lang)
    if not ref:
        return 1.0 if not hyp else 0.0
    if lang == "zh":
        return max(0.0, 1.0 - cer(ref, hyp))
    return max(0.0, 1.0 - wer(ref, hyp))


def model_dense_size_mb(model: torch.nn.Module) -> float:
    return sum(p.numel() * p.element_size() for p in model.parameters()) / (1024 * 1024)


def linear_sparsity(model: torch.nn.Module) -> float:
    zeros = 0
    total = 0
    for module in model.modules():
        if isinstance(module, torch.nn.Linear):
            weight = module.weight.detach()
            zeros += int((weight == 0).sum().item())
            total += weight.numel()
    return zeros / total if total else 0.0


def generate_text(
    model: WhisperForConditionalGeneration,
    processor: WhisperProcessor,
    sample: Sample,
    device: torch.device,
    max_new_tokens: int,
) -> str:
    audio = load_audio(sample.audio_path)
    inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
    input_features = inputs.input_features.to(device)
    if model.dtype == torch.float16:
        input_features = input_features.half()

    language = {"en": "english", "zh": "chinese", "fr": "french"}.get(sample.lang, sample.lang)
    with torch.no_grad():
        try:
            generated = model.generate(
                input_features,
                language=language,
                task="transcribe",
                max_new_tokens=max_new_tokens,
            )
        except TypeError:
            generated = model.generate(input_features, max_new_tokens=max_new_tokens)
    return processor.batch_decode(generated, skip_special_tokens=True)[0].strip()


def evaluate_model(
    method: str,
    model: WhisperForConditionalGeneration,
    processor: WhisperProcessor,
    samples: List[Sample],
    device: torch.device,
    max_new_tokens: int,
    note: str = "",
) -> List[Dict[str, object]]:
    model.eval()
    rows: List[Dict[str, object]] = []
    sparsity = linear_sparsity(model)
    dense_size = model_dense_size_mb(model)
    for sample in tqdm(samples, desc=f"eval {method}"):
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        start = time.perf_counter()
        pred = generate_text(model, processor, sample, device, max_new_tokens)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        latency_ms = (time.perf_counter() - start) * 1000
        audio_sec = len(load_audio(sample.audio_path)) / 16000.0
        rows.append(
            {
                "method": method,
                "language": sample.lang_name,
                "label": sample.label,
                "expected": sample.expected,
                "prediction": pred,
                "accuracy": score_text(sample.expected, pred, sample.lang),
                "latency_ms": latency_ms,
                "audio_sec": audio_sec,
                "rtf": latency_ms / 1000 / audio_sec if audio_sec else np.nan,
                "dense_size_mb": dense_size,
                "linear_sparsity": sparsity,
                "note": note,
            }
        )
    return rows


def build_training_batch(
    processor: WhisperProcessor,
    samples: List[Sample],
    labels: Dict[str, str],
    device: torch.device,
    dtype: torch.dtype,
    index: int,
) -> Dict[str, torch.Tensor]:
    sample = samples[index % len(samples)]
    audio = load_audio(sample.audio_path)
    inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
    input_features = inputs.input_features.to(device)
    if dtype == torch.float16:
        input_features = input_features.half()

    text = labels[sample.label]
    tokenized = processor.tokenizer(text, return_tensors="pt")
    label_ids = tokenized.input_ids.to(device)
    return {"input_features": input_features, "labels": label_ids}


def train_on_pseudo_labels(
    model: WhisperForConditionalGeneration,
    processor: WhisperProcessor,
    samples: List[Sample],
    labels: Dict[str, str],
    device: torch.device,
    steps: int,
    epochs: int,
    lr: float,
    desc: str,
) -> None:
    model.train()
    optimizer = AdamW(model.parameters(), lr=lr)
    dtype = next(model.parameters()).dtype
    total_steps = min(steps, max(1, epochs * len(samples)))
    scaler_enabled = device.type == "cuda" and dtype == torch.float16
    scaler = torch.cuda.amp.GradScaler(enabled=scaler_enabled)

    for step in tqdm(range(total_steps), desc=desc):
        batch = build_training_batch(processor, samples, labels, device, dtype, step)
        optimizer.zero_grad(set_to_none=True)
        with torch.cuda.amp.autocast(enabled=scaler_enabled):
            out = model(**batch)
            loss = out.loss
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
    model.eval()


def apply_global_pruning(model: torch.nn.Module, amount: float) -> None:
    parameters = []
    for module in model.modules():
        if isinstance(module, torch.nn.Linear):
            parameters.append((module, "weight"))
    prune.global_unstructured(parameters, pruning_method=prune.L1Unstructured, amount=amount)
    for module, name in parameters:
        prune.remove(module, name)


def load_whisper(model_name: str, device: torch.device, use_fp16: bool) -> WhisperForConditionalGeneration:
    model = WhisperForConditionalGeneration.from_pretrained(model_name)
    model.config.use_cache = False
    if use_fp16 and device.type == "cuda":
        model = model.half()
    model.to(device)
    return model


def write_report(rows: List[Dict[str, object]], out_dir: Path, args: argparse.Namespace) -> None:
    df = pd.DataFrame(rows)
    summary = (
        df.groupby("method")
        .agg(
            samples=("accuracy", "count"),
            accuracy=("accuracy", "mean"),
            latency_ms=("latency_ms", "mean"),
            rtf=("rtf", "mean"),
            dense_size_mb=("dense_size_mb", "first"),
            linear_sparsity=("linear_sparsity", "first"),
        )
        .reset_index()
        .sort_values(["accuracy", "rtf"], ascending=[False, True])
    )
    df.to_csv(out_dir / "lightweight_methods_results.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(out_dir / "lightweight_methods_summary.csv", index=False, encoding="utf-8-sig")

    lines = [
        "# Lightweight Methods Experiment Report",
        "",
        "## Setup",
        "",
        f"- Teacher: `{args.teacher}`",
        f"- Student: `{args.student}`",
        f"- Samples: {len(df) // max(1, df['method'].nunique())} local benchmark audio files",
        f"- Device: `{torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}`",
        f"- Cache root: `{CACHE_ROOT}`",
        "",
        "## Summary",
        "",
        "| Method | Samples | Accuracy | Latency ms | RTF | Dense size MB | Linear sparsity |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['method']} | {int(row['samples'])} | {row['accuracy']*100:.1f}% | "
            f"{row['latency_ms']:.0f} | {row['rtf']:.2f} | {row['dense_size_mb']:.1f} | "
            f"{row['linear_sparsity']*100:.1f}% |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Notes",
            "",
            "- Distillation is implemented as sequence-level pseudo-label distillation from the teacher model.",
            "- Magnitude pruning creates zero weights, but dense PyTorch/whisper runtimes may not translate that sparsity into speedup.",
            "- Recovery fine-tuning tests whether a pruned student can regain quality after compression.",
            "- These results are PC/GPU-side research evidence; Android deployment still depends on GGML/GGUF conversion and runtime support.",
        ]
    )
    (out_dir / "lightweight_methods_report.md").write_text("\n".join(lines), encoding="utf-8")

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    axes[0].bar(summary["method"], summary["accuracy"] * 100)
    axes[0].set_title("Accuracy")
    axes[0].set_ylabel("%")
    axes[1].bar(summary["method"], summary["rtf"])
    axes[1].set_title("RTF")
    axes[2].bar(summary["method"], summary["linear_sparsity"] * 100)
    axes[2].set_title("Linear sparsity")
    axes[2].set_ylabel("%")
    for ax in axes:
        ax.tick_params(axis="x", rotation=35)
        ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "method_comparison.png", dpi=150)
    plt.close(fig)

    pruning = summary[summary["method"].str.contains("pruned", case=False, regex=False)]
    if not pruning.empty:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.scatter(pruning["linear_sparsity"] * 100, pruning["accuracy"] * 100, s=80)
        for _, row in pruning.iterrows():
            ax.annotate(row["method"], (row["linear_sparsity"] * 100, row["accuracy"] * 100))
        ax.set_xlabel("Linear sparsity (%)")
        ax.set_ylabel("Accuracy (%)")
        ax.set_title("Pruning trade-off")
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(out_dir / "pruning_tradeoff.png", dpi=150)
        plt.close(fig)


def main() -> None:
    args = parse_args()
    if args.smoke:
        args.sample_limit = 3
        args.max_train_steps = min(args.max_train_steps, 3)
        args.prune_amounts = [args.recovery_prune_amount]

    set_seed(args.seed)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for path in [CACHE_ROOT, Path(os.environ["HF_HOME"]), Path(os.environ["TORCH_HOME"])]:
        path.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_fp16 = device.type == "cuda"
    samples = load_samples(args.sample_limit)
    if not samples:
        raise RuntimeError("No local benchmark audio files found.")

    print(f"Device: {device}")
    print(f"Cache root: {CACHE_ROOT}")
    print(f"Samples: {len(samples)}")

    processor = WhisperProcessor.from_pretrained(args.student)
    rows: List[Dict[str, object]] = []

    student = load_whisper(args.student, device, use_fp16)
    rows += evaluate_model("tiny-baseline", student, processor, samples, device, args.max_new_tokens)
    del student
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    pseudo_labels: Dict[str, str] = {}
    if not args.skip_distill:
        teacher_processor = WhisperProcessor.from_pretrained(args.teacher)
        teacher = load_whisper(args.teacher, device, use_fp16)
        for sample in tqdm(samples, desc="teacher pseudo labels"):
            pseudo_labels[sample.label] = generate_text(
                teacher, teacher_processor, sample, device, args.max_new_tokens
            )
        with (out_dir / "pseudo_labels.json").open("w", encoding="utf-8") as f:
            json.dump(pseudo_labels, f, ensure_ascii=False, indent=2)
        del teacher
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        # Keep training models in FP32. Loading the trainable weights directly
        # as FP16 triggers GradScaler unscale errors on Windows/CUDA.
        distilled = load_whisper(args.student, device, use_fp16=False)
        train_on_pseudo_labels(
            distilled,
            processor,
            samples,
            pseudo_labels,
            device,
            args.max_train_steps,
            args.epochs,
            args.learning_rate,
            "distill tiny",
        )
        if use_fp16:
            distilled = distilled.half()
        rows += evaluate_model("distilled-tiny", distilled, processor, samples, device, args.max_new_tokens)

        recovery = load_whisper(args.student, device, use_fp16=False)
        apply_global_pruning(recovery, args.recovery_prune_amount)
        train_on_pseudo_labels(
            recovery,
            processor,
            samples,
            pseudo_labels,
            device,
            args.max_train_steps,
            args.epochs,
            args.learning_rate,
            "pruning recovery",
        )
        apply_global_pruning(recovery, args.recovery_prune_amount)
        if use_fp16:
            recovery = recovery.half()
        rows += evaluate_model(
            f"pruned-{int(args.recovery_prune_amount*100)}-recovery",
            recovery,
            processor,
            samples,
            device,
            args.max_new_tokens,
        )
        del distilled, recovery
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    for amount in args.prune_amounts:
        pruned = load_whisper(args.student, device, use_fp16)
        apply_global_pruning(pruned, amount)
        rows += evaluate_model(
            f"pruned-{int(amount*100)}",
            pruned,
            processor,
            samples,
            device,
            args.max_new_tokens,
        )
        del pruned
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    write_report(rows, out_dir, args)
    print(f"Wrote results to {out_dir}")


if __name__ == "__main__":
    main()
