#!/usr/bin/env python3
"""
ASR-Mobile 模型基准测试脚本
============================
一键测试 models/ 目录下所有 GGML/GGUF 模型的性能。

测试维度:
  - 准确率 (WER/CER)
  - 推理速度 (ms)
  - 实时因子 (RTF)
  - CPU / 内存开销
  - 模型加载时间

输出:
  - benchmark_report.txt      ← 文本报告
  - benchmark_results.csv     ← CSV 数据
  - accuracy_comparison.png   ← 准确率对比图
  - speed_comparison.png      ← 速度对比图
  - memory_comparison.png     ← 内存对比图
  - language_accuracy.png     ← 各语言准确率热图
  - overall_ranking.png       ← 综合排名图

用法:
  conda activate MachineLearning
  cd ASR-Mobile/benchmark_results
  python benchmark_models.py
"""

import os, sys, time, csv, subprocess, json, re, psutil, gc, platform, struct, wave, uuid, unicodedata
from pathlib import Path
from datetime import datetime

# ── 修复 Python SSL（Windows cert store 兼容性问题） ──
try:
    import ssl, certifi
    ssl.SSLContext._load_windows_store_certs = lambda self, s, p: None
    import os as _os
    _os.environ['SSL_CERT_FILE'] = certifi.where()
except Exception:
    pass

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ── 字体配置：sans-serif 为主，附加中文字体做 fallback ──
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei', 'Microsoft YaHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# ─────────────────────────────────────────────
#  配置
# ─────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def has_non_ascii(path):
    try:
        str(path).encode("ascii")
        return False
    except UnicodeEncodeError:
        return True

def find_runtime_project_root():
    env_root = os.environ.get("ASR_BENCH_PROJECT_ROOT")
    if env_root:
        root = Path(env_root)
        if root.exists():
            return root

    if platform.system().lower().startswith("win") and has_non_ascii(PROJECT_ROOT):
        # whisper.cpp on Windows can fail to load models when the path contains
        # non-ASCII characters. Use the junction created for local benchmarking.
        ascii_root = Path(os.environ.get("ASR_BENCH_ASCII_ROOT", r"D:\asr-mobile-bench"))
        if ascii_root.exists():
            return ascii_root

    return PROJECT_ROOT

RUNTIME_PROJECT_ROOT = find_runtime_project_root()
MODELS_DIR = RUNTIME_PROJECT_ROOT / "models"
OUTPUT_DIR = RUNTIME_PROJECT_ROOT / "model_benchmark"

def find_whisper_cli():
    candidates = []
    env_path = os.environ.get("WHISPER_CLI_PATH")
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend([
        RUNTIME_PROJECT_ROOT / "android/app/src/main/cpp/third_party/whisper.cpp/build/bin/whisper-cli.exe",
        RUNTIME_PROJECT_ROOT / "android/app/src/main/cpp/third_party/whisper.cpp/build/bin/Release/whisper-cli.exe",
        PROJECT_ROOT / "android/app/src/main/cpp/third_party/whisper.cpp/build/bin/whisper-cli.exe",
        PROJECT_ROOT / "android/app/src/main/cpp/third_party/whisper.cpp/build/bin/Release/whisper-cli.exe",
        Path(r"C:\Users\96402\AppData\Local\Temp\whisper-bin\Release\whisper-cli.exe"),
    ])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]

WHISPER_CLI = find_whisper_cli()

# 需要测试的模型文件
MODELS = [
    ("Tiny baseline", "ggml-tiny.bin"),
    ("Tiny Q8_0", "ggml-tiny-q8_0.bin"),
    ("Tiny Q5_1", "ggml-tiny-q5_1.bin"),
    ("Tiny Q4_0", "ggml-tiny-q4_0.bin"),
    ("Base baseline", "ggml-base.bin"),
    ("Base Q8_0", "ggml-base-q8_0.bin"),
    ("Base Q5_1", "ggml-base-q5_1.bin"),
    ("Base Q4_0", "ggml-base-q4_0.bin"),
]

MODEL_FILTER = os.environ.get("ASR_BENCH_MODEL_FILTER", "").strip().lower()
if MODEL_FILTER:
    MODELS = [
        (name, filename)
        for name, filename in MODELS
        if MODEL_FILTER in name.lower() or MODEL_FILTER in filename.lower()
    ]

# 测试短语（中英法各3条）
TEST_PHRASES = [
    # (language, language_name, label, expected_text)
    ("en", "English", "Greeting",    "How are you doing today"),
    ("en", "English", "Weather",     "The weather is very nice outside"),
    ("en", "English", "Order",       "I would like a cup of coffee"),
    ("zh", "Chinese",  "Greeting_zh","你好今天天气怎么样"),
    ("zh", "Chinese",  "Order_zh",   "我想订一杯咖啡"),
    ("zh", "Chinese",  "Thanks",     "谢谢你的帮助"),
    ("fr", "French",   "Salutation", "Bonjour comment allez vous"),
    ("fr", "French",   "Commande",   "Je voudrais un cafe"),
    ("fr", "French",   "Thanks_fr",  "Merci pour votre aide"),
]

N_WARMUP = 1  # 每条短语预热次数（不计入结果）
N_RUNS   = 3  # 每条短语正式测试次数（取中位数）


# ─────────────────────────────────────────────
#  WER / CER 计算
# ─────────────────────────────────────────────

def levenshtein(ref, hyp):
    """编辑距离（两行优化）"""
    m, n = len(ref), len(hyp)
    prev = list(range(n + 1))
    curr = [0] * (n + 1)
    for i in range(1, m + 1):
        curr[0] = i
        for j in range(1, n + 1):
            cost = 0 if ref[i-1] == hyp[j-1] else 1
            curr[j] = min(prev[j] + 1, curr[j-1] + 1, prev[j-1] + cost)
        prev, curr = curr, prev
    return prev[n]

def normalize_text(text, language):
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    if language == "zh":
        return re.sub(r"[^\w\u4e00-\u9fff]", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def compute_wer(reference, hypothesis):
    """词错误率（英文等空格分隔语言）"""
    ref = reference.strip().split()
    hyp = hypothesis.strip().split()
    if not ref:
        return 0.0 if not hyp else 1.0
    return levenshtein(ref, hyp) / len(ref)

def compute_cer(reference, hypothesis):
    """字错误率（中文等按字符理解的语言）"""
    if not reference:
        return 0.0 if not hypothesis else 1.0
    return levenshtein(list(reference), list(hypothesis)) / len(reference)

def accuracy(reference, hypothesis, language):
    """准确率 0~1"""
    reference = normalize_text(reference, language)
    hypothesis = normalize_text(hypothesis, language)
    if language == "zh":
        return max(0, 1 - compute_cer(reference, hypothesis))
    else:
        return max(0, 1 - compute_wer(reference, hypothesis))


# ─────────────────────────────────────────────
#  音频生成
# ─────────────────────────────────────────────

def _ensure_ffmpeg():
    """确保 ffmpeg 在 PATH 中（conda 环境可能没自动加）"""
    for _root in [os.environ.get('CONDA_PREFIX', ''), sys.prefix]:
        _ff = os.path.join(_root, 'Library', 'bin', 'ffmpeg.exe')
        if os.path.exists(_ff):
            os.environ['PATH'] = os.path.dirname(_ff) + os.pathsep + os.environ.get('PATH', '')
            return True
    return False

def generate_test_audio(output_dir):
    """用 gTTS + pydub 生成所有测试音频"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_files = []
    missing = []
    for item in TEST_PHRASES:
        lang, lang_name, label, text = item
        filepath = output_dir / f"{lang}_{label}.wav"
        if filepath.exists() and filepath.stat().st_size > 1000:
            print(f"  [OK] {filepath.name} already exists")
            audio_files.append((lang, lang_name, label, text, str(filepath)))
        else:
            missing.append(item)

    if not missing:
        return audio_files

    _ensure_ffmpeg()
    try:
        from gtts import gTTS
        from pydub import AudioSegment
    except ImportError as e:
        raise RuntimeError(
            "Some test audio files are missing, and gTTS/pydub are not installed. "
            "Install them or restore model_benchmark/test_audio/*.wav."
        ) from e

    for lang, lang_name, label, text in missing:
        filename = f"{lang}_{label}.wav"
        filepath = output_dir / filename

        # 语言代码映射
        tts_lang = "zh-CN" if lang == "zh" else lang

        try:
            # gTTS 生成 MP3
            tts = gTTS(text=text, lang=tts_lang.split("-")[0], tld="com", slow=False)
            mp3_path = filepath.with_suffix(".mp3")
            tts.save(str(mp3_path))

            # 转 16kHz 16bit mono WAV
            audio = AudioSegment.from_mp3(str(mp3_path))
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            audio.export(str(filepath), format="wav")
            mp3_path.unlink()  # 删除临时 MP3

            dur = len(audio) / 1000
            sz = filepath.stat().st_size / 1024
            print(f"  [OK] {filename}  ({sz:.0f} KB, {dur:.1f}s)")
            audio_files.append((lang, lang_name, label, text, str(filepath)))
        except Exception as e:
            # 重试一次
            print(f"  [WARN] {filename}: {e}, retrying...")
            try:
                time.sleep(2)
                tts = gTTS(text=text, lang=tts_lang.split("-")[0], tld="com", slow=False)
                mp3_path = filepath.with_suffix(".mp3")
                tts.save(str(mp3_path))
                audio = AudioSegment.from_mp3(str(mp3_path))
                audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                audio.export(str(filepath), format="wav")
                mp3_path.unlink()
                dur = len(audio) / 1000
                sz = filepath.stat().st_size / 1024
                print(f"  [OK] {filename} (retry OK, {sz:.0f} KB, {dur:.1f}s)")
                audio_files.append((lang, lang_name, label, text, str(filepath)))
            except Exception as e2:
                print(f"  [FAIL] {filename} (retry failed): {e2}")

    return audio_files


# ─────────────────────────────────────────────
#  模型推理（调用 whisper-cli）
# ─────────────────────────────────────────────

def run_whisper(model_path, audio_path, n_threads=4):
    """运行 whisper-cli 返回 (转录文本, 耗时_ms)"""
    tmp_dir = OUTPUT_DIR / "_tmp_transcripts"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    output_base = tmp_dir / f"whisper_{os.getpid()}_{uuid.uuid4().hex}"
    output_txt = output_base.with_suffix(".txt")

    start = time.perf_counter()

    result = subprocess.run(
        [
            str(WHISPER_CLI),
            "--model", str(model_path),
            "--file", str(audio_path),
            "--threads", str(n_threads),
            "--language", "auto",
            "--no-timestamps",
            "--no-prints",
            "--output-txt",
            "--output-file", str(output_base),
        ],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300
    )
    elapsed_ms = (time.perf_counter() - start) * 1000

    transcript = ""
    if output_txt.exists():
        transcript = output_txt.read_text(encoding="utf-8", errors="ignore").strip()

    if not transcript:
        lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
        lines = [
            line for line in lines
            if not line.startswith(("whisper_", "main:", "read_audio_data:", "system_info:"))
        ]
        transcript = " ".join(lines).strip()

    if not transcript and result.returncode != 0:
        err = (result.stderr or result.stdout).strip()
        transcript = f"[whisper-cli failed: {err[:160]}]" if err else "[whisper-cli failed]"

    if not transcript:
        transcript = "[No speech detected]"

    try:
        output_txt.unlink(missing_ok=True)
    except Exception:
        pass

    return transcript, elapsed_ms


def get_memory_usage():
    """获取当前进程的内存使用（MB）"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


# ─────────────────────────────────────────────
#  模型加载时间
# ─────────────────────────────────────────────

def measure_load_time(model_path):
    """通过 whisper-cli 测量模型加载时间（用空音频快速触发加载）"""
    # 生成一个极短的静音音频
    tmp_wav = Path(OUTPUT_DIR) / "_load_test.wav"

    with wave.open(str(tmp_wav), 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        # 0.1 秒静音
        for _ in range(1600):
            wf.writeframes(struct.pack('<h', 0))

    gc.collect()
    start = time.perf_counter()
    run_whisper(model_path, str(tmp_wav))
    load_ms = (time.perf_counter() - start) * 1000

    tmp_wav.unlink()
    return load_ms


# ─────────────────────────────────────────────
#  主测试循环
# ─────────────────────────────────────────────

def benchmark_all_models(audio_files):
    """对所有模型执行完整基准测试"""
    results = {}

    for display_name, model_filename in MODELS:
        model_path = MODELS_DIR / model_filename
        if not model_path.exists():
            print(f"\n  [WARN] {model_filename} 不存在，跳过")
            continue

        model_size_mb = model_path.stat().st_size / (1024 * 1024)
        print(f"\n{'='*60}")
        print(f"[MODEL] {display_name}")
        print(f"   文件: {model_filename}  ({model_size_mb:.0f} MB)")

        # ── 加载时间 ──
        print(f"   测量加载时间...")
        load_times = []
        for _ in range(3):
            load_times.append(measure_load_time(model_path))
        load_time_ms = np.median(load_times)
        print(f"   加载时间: {load_time_ms:.0f} ms")

        # ── 逐条测试 ──
        model_results = []
        total = len(audio_files)

        for idx, (lang, lang_name, label, expected, audio_path) in enumerate(audio_files):
            sys.stdout.write(f"\r    [{idx+1}/{total}] {lang_name} - {label}... ")
            sys.stdout.flush()

            # 预热
            for _ in range(N_WARMUP):
                run_whisper(model_path, audio_path)

            # 正式测试（多次取中位数）
            transcripts = []
            times = []

            for _ in range(N_RUNS):
                gc.collect()
                mem_before = get_memory_usage()
                t, elapsed = run_whisper(model_path, audio_path)
                mem_after = get_memory_usage()
                transcripts.append(t)
                times.append(elapsed)

            # 取中位数
            mid = np.argsort(times)[len(times) // 2]
            transcript = transcripts[mid]
            inference_ms = times[mid]
            memory_delta = mem_after - mem_before

            # 准确率
            acc = accuracy(expected, transcript, lang)

            # WAV 时长估算
            try:
                with wave.open(audio_path, 'r') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    audio_sec = frames / rate
            except:
                audio_sec = 0

            rtf = inference_ms / 1000 / audio_sec if audio_sec > 0 else float('nan')

            model_results.append({
                'language': lang,
                'language_name': lang_name,
                'label': label,
                'expected': expected,
                'transcript': transcript,
                'inference_ms': inference_ms,
                'audio_sec': audio_sec,
                'rtf': rtf,
                'accuracy': acc,
                'memory_delta_mb': memory_delta,
            })

            if acc < 0.3:
                sys.stdout.write(f"[LOW] acc={acc:.0%} (expected: '{expected}', got: '{transcript[:50]}')")
            else:
                sys.stdout.write(f"[OK] acc={acc:.0%}  {inference_ms:.0f}ms")
            sys.stdout.flush()

        print()

        results[display_name] = {
            'model_name': display_name,
            'model_filename': model_filename,
            'model_size_mb': model_size_mb,
            'load_time_ms': load_time_ms,
            'results': model_results,
        }

    return results


# ─────────────────────────────────────────────
#  汇总与可视化
# ─────────────────────────────────────────────

def compute_summary(results):
    """计算各模型的汇总指标"""
    summaries = []
    for model_name, data in results.items():
        rs = data['results']
        accs = [r['accuracy'] for r in rs]
        times = [r['inference_ms'] for r in rs]
        rtfs = [r['rtf'] for r in rs if not np.isnan(r['rtf'])]
        mems = [r['memory_delta_mb'] for r in rs]

        # 按语言分组准确率
        lang_acc = {}
        for r in rs:
            lang_acc.setdefault(r['language_name'], []).append(r['accuracy'])
        lang_acc = {k: np.mean(v) for k, v in lang_acc.items()}

        avg_acc = np.mean(accs)
        avg_time = np.mean(times)
        avg_rtf = np.mean(rtfs) if rtfs else 0
        avg_mem = np.mean(mems)

        summaries.append({
            'model_name': model_name,
            'model_filename': data['model_filename'],
            'model_size_mb': data['model_size_mb'],
            'load_time_ms': data['load_time_ms'],
            'avg_accuracy': avg_acc * 100,
            'avg_inference_ms': avg_time,
            'avg_rtf': avg_rtf,
            'avg_memory_mb': avg_mem,
            'lang_accuracy': lang_acc,
            'results': rs,
        })

    # 综合评分（准确率 60% + 速度 40%）
    if summaries:
        best_acc = max(s['avg_accuracy'] for s in summaries)
        worst_acc = min(s['avg_accuracy'] for s in summaries)
        best_speed = min(s['avg_inference_ms'] for s in summaries)
        worst_speed = max(s['avg_inference_ms'] for s in summaries)

        for s in summaries:
            acc_score = (s['avg_accuracy'] - worst_acc) / (best_acc - worst_acc) if best_acc > worst_acc else 1.0
            speed_score = (worst_speed - s['avg_inference_ms']) / (worst_speed - best_speed) if worst_speed > best_speed else 1.0
            s['overall_score'] = acc_score * 0.6 + speed_score * 0.4

    return summaries


def plot_accuracy(summaries, output_dir):
    """准确率对比图"""
    fig, ax = plt.subplots(figsize=(10, 6))
    # 用短名称替代，避免中文/换行问题
    names = [s['model_name'].replace(' (Multi-lang)','').replace(' (English)','') for s in summaries]
    values = [s['avg_accuracy'] for s in summaries]
    colors = plt.cm.tab20(np.linspace(0, 1, max(len(summaries), 1)))

    bars = ax.barh(names, values, color=colors, height=0.5)
    for bar, v in zip(bars, values):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f'{v:.1f}%', va='center', fontsize=12)

    ax.set_xlabel('Accuracy (%)', fontsize=12)
    ax.set_title('Model Accuracy Comparison', fontsize=16, fontweight='bold')
    ax.set_xlim(0, 110)
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    fig.savefig(output_dir / 'accuracy_comparison.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] accuracy_comparison.png")


def plot_speed(summaries, output_dir):
    """速度对比图（推理时间 + RTF 双轴）"""
    fig, ax1 = plt.subplots(figsize=(10, 6))
    names = [s['model_name'].replace(' (Multi-lang)','').replace(' (English)','') for s in summaries]

    x = np.arange(len(names))
    w = 0.35

    times = [s['avg_inference_ms'] for s in summaries]
    rtfs = [s['avg_rtf'] for s in summaries]
    colors = plt.cm.tab20(np.linspace(0, 1, max(len(summaries), 1)))

    bars1 = ax1.bar(x - w/2, times, w, color=colors, alpha=0.8, label='Inference (ms)')
    ax1.set_ylabel('Inference Time (ms)', fontsize=12, color='darkblue')
    ax1.set_xticks(x)
    ax1.set_xticklabels(names, fontsize=10)
    ax1.grid(axis='y', alpha=0.3)

    for bar, v in zip(bars1, times):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                f'{v:.0f}', ha='center', fontsize=10)

    ax2 = ax1.twinx()
    bars2 = ax2.bar(x + w/2, rtfs, w, color=colors, alpha=0.4, label='RTF')
    ax2.set_ylabel('Real-Time Factor (RTF)', fontsize=12, color='darkred')

    for bar, v in zip(bars2, rtfs):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{v:.2f}', ha='center', fontsize=9)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

    ax1.set_title('Inference Speed Comparison', fontsize=16, fontweight='bold')
    fig.tight_layout()
    fig.savefig(output_dir / 'speed_comparison.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] speed_comparison.png")


def plot_memory(summaries, output_dir):
    """内存/资源对比图"""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    names_short = [s['model_name'].split(' (')[0] for s in summaries]
    colors = plt.cm.tab20(np.linspace(0, 1, max(len(summaries), 1)))

    # 模型大小
    sizes = [s['model_size_mb'] for s in summaries]
    axes[0].bar(names_short, sizes, color=colors)
    axes[0].set_title('Model Size (MB)', fontsize=14)
    axes[0].set_ylabel('MB')
    for i, v in enumerate(sizes):
        axes[0].text(i, v + 1, f'{v:.0f}MB', ha='center', fontsize=10)

    # 加载时间
    loads = [s['load_time_ms'] / 1000 for s in summaries]
    axes[1].bar(names_short, loads, color=colors)
    axes[1].set_title('Load Time (s)', fontsize=14)
    axes[1].set_ylabel('Seconds')
    for i, v in enumerate(loads):
        axes[1].text(i, v + 0.1, f'{v:.1f}s', ha='center', fontsize=10)

    # 推理时内存增量
    mems = [s['avg_memory_mb'] for s in summaries]
    axes[2].bar(names_short, mems, color=colors)
    axes[2].set_title('Inference Memory Δ (MB)', fontsize=14)
    axes[2].set_ylabel('MB')
    for i, v in enumerate(mems):
        axes[2].text(i, v + 0.5, f'{v:.1f}MB', ha='center', fontsize=10)

    for ax in axes:
        ax.tick_params(axis='x', rotation=15)
        ax.grid(axis='y', alpha=0.3)

    fig.suptitle('Resource Usage Comparison', fontsize=16, fontweight='bold')
    fig.tight_layout()
    fig.savefig(output_dir / 'resource_comparison.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] resource_comparison.png")


def plot_language_accuracy(summaries, output_dir):
    """各语言准确率热图"""
    all_langs = ['English', 'Chinese', 'French']
    model_names = [s['model_name'].replace(' (Multi-lang)','').replace(' (English)','') for s in summaries]

    data = np.zeros((len(model_names), len(all_langs)))
    for i, s in enumerate(summaries):
        for j, lang in enumerate(all_langs):
            data[i, j] = s['lang_accuracy'].get(lang, 0) * 100

    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(data, cmap='RdYlGn', vmin=0, vmax=100, aspect='auto')

    ax.set_xticks(range(len(all_langs)))
    ax.set_xticklabels(all_langs, fontsize=12)
    ax.set_yticks(range(len(model_names)))
    ax.set_yticklabels(model_names, fontsize=10)

    for i in range(len(model_names)):
        for j in range(len(all_langs)):
            val = data[i, j]
            color = 'white' if val < 40 else 'black'
            ax.text(j, i, f'{val:.1f}%', ha='center', va='center', fontsize=11, color=color)

    ax.set_title('Accuracy by Language (%)', fontsize=16, fontweight='bold')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(output_dir / 'language_accuracy.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] language_accuracy.png")


def plot_overall_ranking(summaries, output_dir):
    """综合排名图"""
    fig, ax = plt.subplots(figsize=(10, 6))

    sorted_s = sorted(summaries, key=lambda s: s['overall_score'], reverse=True)
    names = [s['model_name'] for s in sorted_s]
    scores = [s['overall_score'] * 100 for s in sorted_s]
    colors = plt.cm.tab20(np.linspace(0, 1, max(len(summaries), 1)))

    bars = ax.barh(names, scores, color=colors, height=0.5)
    for bar, v in zip(bars, scores):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                f'{v:.1f}%', va='center', fontsize=13, fontweight='bold')

    # 排名标签
    rank_labels = [f"#{i+1}" for i in range(len(summaries))]
    for i, (bar, rank) in enumerate(zip(bars, rank_labels)):
        ax.text(bar.get_width() / 2, bar.get_y() + bar.get_height()/2,
                rank, ha='center', va='center', fontsize=14,
                fontweight='bold', color='white' if scores[i] > 40 else 'black')

    ax.set_xlabel('Overall Score (%)', fontsize=12)
    ax.set_title('Overall Model Ranking', fontsize=18, fontweight='bold')
    ax.set_xlim(0, 110)
    ax.grid(axis='x', alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_dir / 'overall_ranking.png', dpi=150)
    plt.close(fig)
    print(f"  [OK] overall_ranking.png")


def write_report(summaries, output_dir):
    """写入文本报告和 CSV"""
    # ── 文本报告 ──
    lines = []
    lines.append("=" * 60)
    lines.append("  ASR Mobile — 模型基准测试报告")
    lines.append("=" * 60)
    lines.append(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"  主机: {platform.node()}")
    lines.append(f"  CPU:  {platform.processor()}")
    lines.append(f"  系统: {platform.system()} {platform.release()}")
    lines.append(f"  Python: {sys.version.split()[0]}")
    lines.append(f"  whisper-cli: {WHISPER_CLI}")
    lines.append("")

    lines.append("-" * 60)
    lines.append("  Overall ranking")
    lines.append("-" * 60)
    sorted_s = sorted(summaries, key=lambda s: s['overall_score'], reverse=True)
    for i, s in enumerate(sorted_s):
        rank = f"{i+1}."
        lines.append(f"  {rank}  {s['model_name']}")
        lines.append(f"      综合得分: {s['overall_score']*100:.1f}%")
        lines.append(f"      准确率:   {s['avg_accuracy']:.1f}%")
        lines.append(f"      推理速度: {s['avg_inference_ms']:.0f} ms")
        lines.append(f"      模型大小: {s['model_size_mb']:.0f} MB")
        lines.append("")

    lines.append("-" * 60)
    lines.append("  Detailed Results")
    lines.append("-" * 60)

    for s in sorted_s:
        lines.append("")
        lines.append(f"  ▶ {s['model_name']}")
        lines.append(f"    文件: {s['model_filename']}  ({s['model_size_mb']:.0f} MB)")
        lines.append(f"    加载时间: {s['load_time_ms']:.0f} ms")
        lines.append(f"    平均推理: {s['avg_inference_ms']:.0f} ms")
        lines.append(f"    平均 RTF: {s['avg_rtf']:.3f}")
        lines.append(f"    平均准确率: {s['avg_accuracy']:.1f}%")
        lines.append(f"    推理内存增量: {s['avg_memory_mb']:.1f} MB")

        for lang, acc in s['lang_accuracy'].items():
            lines.append(f"    {lang}: {acc*100:.1f}%")

        lines.append("")
        lines.append("    Per-phrase results:")
        for r in s['results']:
            acc_str = f"{r['accuracy']*100:.0f}%"
            marker = "!" if r['accuracy'] < 0.3 else "+"
            lines.append(f"      {marker} [{r['language_name']}] {r['label']:12s} -> acc={acc_str:>4s}  {r['inference_ms']:6.0f}ms  RTF={r['rtf']:.2f}")
            lines.append(f"             Expected: {r['expected']}")
            lines.append(f"             Got:      {r['transcript'][:80]}")

    lines.append("")
    lines.append("=" * 60)
    lines.append("  报告完")
    lines.append("=" * 60)

    report_text = "\n".join(lines)
    report_path = output_dir / "benchmark_report.txt"
    report_path.write_text(report_text, encoding='utf-8')
    print(f"  [OK] benchmark_report.txt")

    # ── CSV ──
    csv_path = output_dir / "benchmark_results.csv"
    with open(str(csv_path), 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['Model', 'ModelFile', 'ModelSizeMB', 'LoadTimeMs',
                         'Language', 'Label', 'Expected', 'Transcript',
                         'Accuracy%', 'InferenceMs', 'RTF', 'AudioSec', 'MemoryDeltaMB'])
        for s in summaries:
            for r in s['results']:
                writer.writerow([
                    s['model_name'], s['model_filename'],
                    f"{s['model_size_mb']:.2f}", f"{s['load_time_ms']:.0f}",
                    r['language_name'], r['label'],
                    r['expected'], r['transcript'],
                    f"{r['accuracy']*100:.1f}", f"{r['inference_ms']:.0f}",
                    f"{r['rtf']:.3f}", f"{r['audio_sec']:.1f}",
                    f"{r['memory_delta_mb']:.2f}"
                ])
    print(f"  [OK] benchmark_results.csv")


def print_summary_table(summaries):
    """在控制台输出简洁对比表"""
    print()
    print("=" * 80)
    print("  Quick comparison")
    print("=" * 80)
    print(f"  {'Model':35s} {'Size':>6s} {'Accuracy':>9s} {'Speed':>8s} {'RTF':>6s} {'MemΔ':>6s} {'Load':>7s}")
    print(f"  {'-'*35} {'-'*6} {'-'*9} {'-'*8} {'-'*6} {'-'*6} {'-'*7}")

    ranking = sorted(summaries, key=lambda s: s['overall_score'], reverse=True)
    for i, s in enumerate(ranking):
        if i == 0:
            rank = '#1'
        elif i == 1 and len(ranking) > 1:
            rank = '#2'
        elif i == 2 and len(ranking) > 2:
            rank = '#3'
        else:
            rank = '  '
        print(f"  {rank} {s['model_name']:33s} {s['model_size_mb']:5.0f}MB {s['avg_accuracy']:7.1f}% {s['avg_inference_ms']:7.0f}ms {s['avg_rtf']:5.2f} {s['avg_memory_mb']:5.1f}MB {s['load_time_ms']:6.0f}ms")


# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────

def main():
    os.chdir(str(PROJECT_ROOT))
    print("ASR Mobile model benchmark")
    print(f"   工作目录: {PROJECT_ROOT}")
    print(f"   输出目录: {OUTPUT_DIR}")
    print(f"   模型目录: {MODELS_DIR}")
    print()

    # ── 检查 whisper-cli ──
    if not WHISPER_CLI.exists():
        print(f"[FAIL] whisper-cli 未找到: {WHISPER_CLI}")
        print("   请下载: https://github.com/ggml-org/whisper.cpp/releases/tag/v1.9.0")
        sys.exit(1)

    # ── 检查模型 ──
    available_models = []
    for display_name, model_filename in MODELS:
        model_path = MODELS_DIR / model_filename
        if model_path.exists():
            sz = model_path.stat().st_size / (1024*1024)
            available_models.append((display_name, model_filename))
            print(f"  [OK] {display_name}: {model_filename} ({sz:.0f} MB)")
        else:
            print(f"  [MISSING] {display_name}: {model_filename} - 不存在")

    if not available_models:
        print("\n[FAIL] 没有可测试的模型！")
        sys.exit(1)

    # ── 生成测试音频 ──
    print("\nPreparing test audio...")
    audio_dir = OUTPUT_DIR / "test_audio"
    audio_files = generate_test_audio(audio_dir)
    print(f"   共 {len(audio_files)} 条测试短语")

    # ── 运行 benchmark ──
    print("\nStarting benchmark...")
    print(f"   预热: {N_WARMUP} 次/条  |  正式: {N_RUNS} 次/条")
    all_results = benchmark_all_models(audio_files)

    # ── 汇总 ──
    print("\nGenerating report and plots...")
    summaries = compute_summary(all_results)

    if summaries:
        write_report(summaries, OUTPUT_DIR)
        print()
        plot_accuracy(summaries, OUTPUT_DIR)
        plot_speed(summaries, OUTPUT_DIR)
        plot_memory(summaries, OUTPUT_DIR)
        plot_language_accuracy(summaries, OUTPUT_DIR)
        plot_overall_ranking(summaries, OUTPUT_DIR)
        print_summary_table(summaries)

    print("\nAll tests completed.")
    print(f"   报告: {OUTPUT_DIR / 'benchmark_report.txt'}")
    print(f"   输出图表: *.png")


if __name__ == '__main__':
    main()
