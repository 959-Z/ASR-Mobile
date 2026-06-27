# Quantization Analysis for Android Offline ASR

## Goal

This experiment evaluates whether GGML quantization can reduce Whisper model size and runtime cost while keeping recognition quality acceptable for Android offline ASR. The tested model families are `tiny` and `base`, each compared across baseline, Q8, Q5, and Q4 variants.

The PC benchmark is used as a model screening step. It is not a replacement for Android device testing, because mobile CPU, memory bandwidth, ABI, and thermal behavior can change the final ranking.

## Setup

- Runtime: `whisper-cli.exe` built from the project `whisper.cpp` dependency.
- Model directory: `models/`.
- Test audio: 9 short WAV files in `evaluation/pc_benchmark/test_audio/`.
- Languages: English x 3, Chinese x 3, French x 3.
- Runs: 1 warmup run and 3 measured runs per audio sample.
- Metrics: model size, loading time, inference time, RTF, memory delta, and text accuracy.
- Output files: `evaluation/pc_benchmark/benchmark_results.csv`, `benchmark_report.txt`, and comparison plots.

On Windows, the benchmark uses the ASCII junction `D:\asr-mobile-bench` to avoid `whisper-cli` model loading failures caused by non-ASCII project paths.

## Model Matrix and Results

| Model | File | Size MB | Size vs baseline | Load ms | Inference ms | RTF | Accuracy |
|---|---|---:|---:|---:|---:|---:|---:|
| Tiny baseline | `ggml-tiny.bin` | 74.09 | 100.0% | 399 | 712 | 0.37 | 83.2% |
| Tiny Q8_0 | `ggml-tiny-q8_0.bin` | 41.52 | 56.0% | 367 | 599 | 0.31 | 83.2% |
| Tiny Q5_1 | `ggml-tiny-q5_1.bin` | 30.66 | 41.4% | 422 | 792 | 0.40 | 83.2% |
| Tiny Q4_0 | `ggml-tiny-q4_0.bin` | 24.15 | 32.6% | 294 | 525 | 0.27 | 90.1% |
| Base baseline | `ggml-base.bin` | 141.10 | 100.0% | 867 | 1692 | 0.87 | 92.9% |
| Base Q8_0 | `ggml-base-q8_0.bin` | 77.98 | 55.3% | 629 | 1205 | 0.62 | 92.9% |
| Base Q5_1 | `ggml-base-q5_1.bin` | 56.94 | 40.4% | 781 | 1541 | 0.79 | 92.9% |
| Base Q4_0 | `ggml-base-q4_0.bin` | 44.32 | 31.4% | 542 | 1087 | 0.56 | 98.4% |

Language-level accuracy:

| Model | English | Chinese | French |
|---|---:|---:|---:|
| Tiny baseline | 100.0% | 57.9% | 91.7% |
| Tiny Q8_0 | 100.0% | 57.9% | 91.7% |
| Tiny Q5_1 | 100.0% | 57.9% | 91.7% |
| Tiny Q4_0 | 100.0% | 78.6% | 91.7% |
| Base baseline | 100.0% | 78.6% | 100.0% |
| Base Q8_0 | 100.0% | 78.6% | 100.0% |
| Base Q5_1 | 100.0% | 78.6% | 100.0% |
| Base Q4_0 | 100.0% | 95.2% | 100.0% |

## Findings

Q8 is the safest compression level in terms of quality. In this benchmark, Tiny Q8_0 keeps the same average accuracy as Tiny baseline while reducing file size by 44.0%. Base Q8_0 also keeps the same average accuracy as Base baseline while reducing file size by 44.7% and improving average inference time from 1692 ms to 1205 ms.

Q5 is not automatically the best speed-size trade-off on this CPU. Although Q5_1 reduces the model file to about 40% of the baseline size for both model families, it is slower than Q8_0 in this run. This suggests that quantized model size and runtime speed are not linearly related; the actual CPU kernel implementation matters.

Q4 gives the strongest compression. Tiny Q4_0 is only 24.15 MB and reaches RTF 0.27, making it the best low-resource candidate. Base Q4_0 is 44.32 MB and reaches the highest accuracy in this short-audio test, but it still takes about 1087 ms per sample, roughly twice the Tiny Q4_0 inference time.

Base models are more robust on multilingual quality, especially Chinese and French, but the cost is higher. Base Q4_0 is the best quality candidate in this test, while Tiny Q4_0 is the best deployment-efficiency candidate.

## Relation to Other Lightweight Methods

Quantization is not the only compression path. This project also tested pseudo-label distillation, magnitude pruning, and pruning recovery fine-tuning in `lightweight_experiments/`. The GPU-side experiment showed that a distilled tiny student can improve quality on the short benchmark, and that recovery fine-tuning can recover part of the quality loss after pruning.

However, quantization remains the main Android deployment method because it is directly supported by whisper.cpp GGML models. Distillation requires training and then model conversion before Android use. Unstructured pruning creates sparse weights, but dense mobile runtimes do not automatically reduce file size or speed up inference unless sparse kernels or structured pruning are supported.

Therefore, the practical deployment decision is:

- Use GGML Q4/Q8 quantization for the current Android app.
- Treat distillation as a promising quality-improvement direction for future converted models.
- Treat pruning as a research result and negative engineering finding unless a sparse/structured runtime is introduced.

## Recommendation for Android Verification

Use two main candidates for Android loading and benchmark:

1. `ggml-tiny-q4_0.bin`: primary low-resource candidate. It has the smallest size, fastest runtime, and RTF well below 1 on PC.
2. `ggml-base-q4_0.bin`: primary quality candidate. It is much smaller than Base baseline and gives the best multilingual accuracy in this test.

Keep `ggml-base-q8_0.bin` as the conservative fallback if Base Q4_0 shows Android loading or quality problems. Keep `ggml-tiny-q8_0.bin` as the conservative tiny-family fallback.

## Limitations

- The audio set is small: only 9 short, clean samples. The results show a trend, not a final production benchmark.
- PC runtime does not directly represent Android runtime.
- Memory delta is measured from the Python benchmark process and should be treated as a rough indicator only.
- The Chinese metric is strict character-level matching. Simplified/traditional character differences can reduce the score even when the semantic content is close.
- No noisy speech, long-form speech, speaker variation, or real mobile microphone recordings are included yet.

## Next Step

B should run Android-side validation in this order:

1. `ggml-tiny-q4_0.bin`
2. `ggml-base-q4_0.bin`
3. `ggml-base-q8_0.bin`
4. `ggml-tiny-q8_0.bin`

For each model, record whether it can be selected, loaded, and used for transcription, then collect loading time, inference time, RTF, memory behavior, and any native crash logs.
