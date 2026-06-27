# Day 2 Model Quantization Plan

## A role objective

A is responsible for preparing a comparable, explainable, and recordable model set for Android-side validation.

The goal for day 2 is to prepare `tiny` and `base` Whisper GGML models, record each model's source, quantization level, file size, expected role, and hand the ready files to B for Android loading validation.

## Baseline

The Android baseline is the bundled multilingual Whisper tiny model:

| Field | Value |
|---|---|
| Model | Whisper tiny |
| Quantization | baseline / existing GGML |
| File name | `ggml-tiny.bin` |
| Repo model path | `models/ggml-tiny.bin` |
| Android asset path | `android/app/src/main/assets/models/ggml-tiny.bin` |
| Size | 74.09 MiB |
| Role | Android baseline |
| Notes | Current built-in APK model and reference point for size reduction |

This baseline is used to compare later quantized models in file size, loading behavior, inference time, memory pressure, and recognition quality.

## Model Matrix

| ID | Model | Quantization | File name | Size MiB | Size vs tiny baseline | Source | Status | Send to B |
|---|---|---|---|---:|---:|---|---|---|
| M0 | tiny | baseline | `ggml-tiny.bin` | 74.09 | 100.00% | repo assets / ggerganov whisper.cpp format | ready | yes |
| M1 | tiny | Q8_0 | `ggml-tiny-q8_0.bin` | 41.52 | 56.05% | `ggerganov/whisper.cpp` via hf-mirror | ready | yes |
| M2 | tiny | Q5_1 | `ggml-tiny-q5_1.bin` | 30.66 | 41.38% | `ggerganov/whisper.cpp` via hf-mirror | ready | yes |
| M3 | tiny | Q4_0 | `ggml-tiny-q4_0.bin` | 24.15 | 32.59% | `Pomni/whisper-tiny-ggml-allquants` via hf-mirror | ready | yes |
| M4 | base | baseline | `ggml-base.bin` | 141.10 | 190.45% | `ggerganov/whisper.cpp` via hf-mirror | ready | yes |
| M5 | base | Q8_0 | `ggml-base-q8_0.bin` | 77.98 | 105.25% | `ggerganov/whisper.cpp` via hf-mirror | ready | yes |
| M6 | base | Q5_1 | `ggml-base-q5_1.bin` | 56.94 | 76.86% | `ggerganov/whisper.cpp` via hf-mirror | ready | yes |
| M7 | base | Q4_0 | `ggml-base-q4_0.bin` | 44.32 | 59.81% | `Pomni/whisper-base-ggml-allquants` via hf-mirror | ready | yes |

All files are stored in `models/`.

`Q5_1` is treated as the Q5 category in the report because it is a 5-bit quantization format. The exact quantization name is preserved in file names and the table to avoid confusion with `q5_0`.

## Quantization Rationale

This project uses quantization as the primary model compression method because it does not require retraining and is practical within a short course project timeline.

Quantization reduces model size and memory pressure by lowering the precision used to represent model weights. In this model set:

| Level | Expected role | Why it is included |
|---|---|---|
| Q8 | Conservative compression | Usually preserves quality better while still reducing file size |
| Q5 | Balanced option | Useful for finding the trade-off between size, speed, memory, and quality |
| Q4 | Aggressive compression | Tests the smallest practical model for lower-resource devices |

The `tiny` series shows the effect of quantization on a small mobile-friendly model. The `base` series adds a model-scale comparison, helping answer whether the higher-quality model is worth the extra size and Android loading cost.

## Android Validation Hand-off

B should validate model loading in this order:

1. `ggml-tiny-q8_0.bin`
2. `ggml-tiny-q5_1.bin`
3. `ggml-tiny-q4_0.bin`
4. `ggml-base-q8_0.bin`
5. `ggml-base-q5_1.bin`
6. `ggml-base-q4_0.bin`
7. `ggml-base.bin`

The order starts with the most stable tiny variants, then moves to base quantized models, and leaves unquantized base last because it is the largest.

For each Android validation run, record:

| Field | Notes |
|---|---|
| Model file | Exact file name |
| File size | MiB |
| Device | Phone model |
| Android version | System version |
| ABI | Example: `arm64-v8a` |
| Selectable in app | yes / no |
| Load model result | success / failed |
| Error message | Full message if failed |
| Basic transcription result | Only if loading succeeds |

## Third-day Benchmark Recommendation

For day 3, benchmark English and Chinese 10-second audio using:

| Priority | Models |
|---|---|
| Required | `ggml-tiny.bin`, `ggml-tiny-q8_0.bin`, `ggml-tiny-q5_1.bin`, `ggml-tiny-q4_0.bin` |
| Required if Android loading succeeds | `ggml-base-q8_0.bin`, `ggml-base-q5_1.bin` |
| Optional | `ggml-base-q4_0.bin`, `ggml-base.bin` |

The benchmark metrics should remain aligned with the day 1 decision:

| Metric | Why it matters |
|---|---|
| Model size | Direct compression benefit |
| Load time | Startup experience on Android |
| Inference time | Whether transcription latency is acceptable |
| RTF | Real-time usability, where RTF < 1 means faster than real time |
| Memory delta | Low-end device feasibility |
| Recognition quality | Whether compression still keeps the model usable |

## Why pruning and distillation are not the day 2 main path

Pruning can remove redundant parameters, but it often needs sparse-kernel support, careful fine-tuning, or extra compatibility work. That is risky for a short Android deployment task.

Distillation can train a smaller model to imitate a larger model, but it requires training data, GPU time, and a more complex evaluation pipeline.

For day 2, whisper.cpp-compatible quantized GGML models are the most direct way to produce Android-testable artifacts and support the course analysis.

## Source Notes

The original model family comes from OpenAI Whisper. The Android-compatible GGML files were obtained from Hugging Face-hosted repositories through `hf-mirror.com`:

| Repository | Used for |
|---|---|
| `ggerganov/whisper.cpp` | tiny/base baseline, Q8, Q5 |
| `Pomni/whisper-tiny-ggml-allquants` | tiny Q4 |
| `Pomni/whisper-base-ggml-allquants` | base Q4 |

The `Pomni` allquants repositories are used only to fill the Q4 variants that are not present in the selected `ggerganov/whisper.cpp` file set.
