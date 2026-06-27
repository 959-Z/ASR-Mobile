# ASR Mobile Project Report

## 1. Problem Statement

This project studies Android offline Automatic Speech Recognition (ASR). The goal is to run speech transcription locally on a mobile device without sending audio to a cloud service. The main technical challenge is that Whisper-style ASR models are accurate but expensive for mobile deployment, where storage, memory, latency, battery, and CPU throughput are limited.

## 2. Research Questions

The project focuses on three questions:

1. Which Whisper model scale is practical for Android offline ASR?
2. How much can quantization reduce model size and runtime cost while preserving recognition quality?
3. Can other lightweight methods, such as distillation and pruning, improve or complement quantization?

## 3. Related Work and Motivation

Whisper provides strong multilingual ASR performance through large-scale weak supervision, making it a suitable baseline for English, Chinese, and French recognition. However, mobile deployment requires compression and runtime optimization.

The main lightweight directions considered in this project are:

- Architecture scaling: using smaller Whisper variants such as `tiny` instead of `base`.
- Post-training quantization: using Q8/Q5/Q4 GGML models supported by whisper.cpp.
- Knowledge distillation: transferring teacher model behavior into a smaller student model.
- Pruning: removing low-importance weights and testing whether sparse models preserve quality.
- Training-based compression recovery: fine-tuning compressed models to recover lost quality.

This project chooses whisper.cpp as the Android runtime because it is C/C++ based, integrates with Android NDK/JNI, and supports GGML quantized models. Python-based desktop runtimes such as faster-whisper and CTranslate2 are important references, but they are less direct for a simple Android app package.

## 4. System Architecture

```text
Android UI
  -> microphone recorder / selected WAV file
  -> local model file manager
  -> Kotlin WhisperEngine wrapper
  -> JNI native backend
  -> whisper.cpp runtime
  -> transcript and benchmark metrics
```

The current Android deployment path uses local model files and native inference. Model selection and compression are evaluated on PC first, then passed to Android validation.

## 5. Lightweight Methods Implemented

| Method | Implementation | Role |
|---|---|---|
| Architecture scaling | `tiny` vs `base` | Compares smaller architecture against larger model capacity |
| GGML quantization | baseline/Q8/Q5/Q4 for `tiny` and `base` | Main Android deployment path |
| Pseudo-label distillation | `openai/whisper-base` teacher -> `openai/whisper-tiny` student | Tests training-based compression |
| Magnitude pruning | 10%, 20%, 30% Linear-layer pruning | Tests sparse compression feasibility |
| Pruning recovery | 20% pruning + short recovery fine-tuning | Tests whether training can recover pruned quality |

## 6. PC Quantization Experiment

The PC quantization experiment tested 8 GGML models on 9 short audio files across English, Chinese, and French.

| Model | Size MB | Load ms | Inference ms | RTF | Accuracy |
|---|---:|---:|---:|---:|---:|
| Tiny baseline | 74.09 | 399 | 712 | 0.37 | 83.2% |
| Tiny Q8_0 | 41.52 | 367 | 599 | 0.31 | 83.2% |
| Tiny Q5_1 | 30.66 | 422 | 792 | 0.40 | 83.2% |
| Tiny Q4_0 | 24.15 | 294 | 525 | 0.27 | 90.1% |
| Base baseline | 141.10 | 867 | 1692 | 0.87 | 92.9% |
| Base Q8_0 | 77.98 | 629 | 1205 | 0.62 | 92.9% |
| Base Q5_1 | 56.94 | 781 | 1541 | 0.79 | 92.9% |
| Base Q4_0 | 44.32 | 542 | 1087 | 0.56 | 98.4% |

The PC benchmark suggests that `ggml-tiny-q4_0.bin` and `ggml-base-q4_0.bin` are attractive candidates because they are small and fast on desktop screening. This screening result is useful, but it must be checked on Android because CPU kernels, JNI overhead, memory behavior, and mobile scheduling can change the ranking.

## 7. Distillation, Pruning, and Training Compression Experiment

A second GPU-side experiment was added to test lightweight methods beyond quantization. The experiment used an NVIDIA GeForce RTX 4060 Laptop GPU, `openai/whisper-base` as teacher, `openai/whisper-tiny` as student, and the same 9 local benchmark audio files.

| Method | Accuracy | Latency ms | RTF | Dense size MB | Linear sparsity |
|---|---:|---:|---:|---:|---:|
| distilled-tiny | 92.9% | 41 | 0.02 | 72.0 | 0.0% |
| pruned-20-recovery | 90.1% | 43 | 0.02 | 72.0 | 20.0% |
| pruned-10 | 89.2% | 86 | 0.04 | 72.0 | 10.0% |
| pruned-20 | 86.9% | 111 | 0.06 | 72.0 | 20.0% |
| tiny-baseline | 83.2% | 94 | 0.05 | 72.0 | 0.0% |
| pruned-30 | 80.7% | 122 | 0.06 | 72.0 | 30.0% |

The distillation result suggests that teacher-generated pseudo labels can improve the small student on the controlled benchmark. Pruning alone gives a visible quality trade-off: 10% and 20% pruning remain usable, while 30% pruning lowers accuracy more clearly. Recovery fine-tuning after 20% pruning improves the pruned model, showing that training-based compression can recover part of the lost quality.

The main negative result is also important: unstructured pruning does not automatically reduce dense checkpoint size or guarantee speedup. Without sparse kernels or structured pruning support, pruning is less deployment-ready than GGML quantization for Android.

## 8. Android Benchmark Method

The Android benchmark validates whether PC-screened models actually work on a phone.

| Field | Value |
|---|---|
| Device | HUAWEI HBN-AL10 |
| Android | 12 |
| ABI | arm64-v8a |
| Audio | 10-second Chinese recording |
| Repetitions | 3 per completed model |

Recommended Android validation order from the PC screening was:

1. `ggml-tiny-q4_0.bin`
2. `ggml-base-q4_0.bin`
3. `ggml-base-q8_0.bin`
4. `ggml-tiny-q8_0.bin`

## 9. Formal Android Benchmark Results

| Model | Quantization | Size MB | Load ms | Avg inference ms | Avg RTF | Result |
|---|---|---:|---:|---:|---:|---|
| `ggml-tiny.bin` | baseline | 74.09 | 400 | 8226.67 | 0.822 | success |
| `ggml-tiny-q8_0.bin` | Q8 | 41.52 | 251 | 40064.67 | 4.006 | success |
| `ggml-tiny-q4_0.bin` | Q4 | 24.15 | 127 in Day 2 loading validation | timeout | timeout | timeout |
| `ggml-tiny-q5_1.bin` | Q5 | 30.66 | 253 | 108814.67 | 10.882 | success |
| `ggml-base-q8_0.bin` | Q8 | 77.98 | 203 | 111234.33 | 11.123 | success |
| `ggml-base-q4_0.bin` | Q4 | 44.32 | 137 in Day 2 loading validation | timeout | timeout | timeout |
| `ggml-base-q5_1.bin` | Q5 | 56.94 | unknown | timeout | timeout | timeout |

The detailed Android benchmark results are stored in [evaluation/android_benchmarks/day4/DAY4_CHINESE_FORMAL_SUMMARY.md](evaluation/android_benchmarks/day4/DAY4_CHINESE_FORMAL_SUMMARY.md).

## 10. Android Recognition Quality

Recognition quality was evaluated with CER and WER against the Chinese reference sentence.

| Model | CER | WER | Quality score |
|---|---:|---:|---:|
| `ggml-tiny.bin` | 0.226 | 0.174 | 4/5 |
| `ggml-tiny-q8_0.bin` | 0.226 | 0.174 | 4/5 |
| `ggml-tiny-q5_1.bin` | 0.283 | 0.239 | 4/5 |
| `ggml-base-q8_0.bin` | 0.358 | 0.413 | 3/5 |

CER uses normalized character-level edit distance. WER uses a token sequence where Chinese characters are treated as individual tokens and English/numeric spans are treated as word tokens. The full scoring output is stored in [evaluation/android_benchmarks/day4/day4-quality-analysis.csv](evaluation/android_benchmarks/day4/day4-quality-analysis.csv).

## 11. Analysis

The PC benchmark and Android benchmark lead to different conclusions. On PC, Q4 models looked strong because they were smaller and fast. On the Huawei Android device, the Q4 models loaded but timed out in the formal benchmark, while Q8/Q5 completed but were much slower than the tiny baseline.

This result is important because model compression does not automatically produce faster mobile inference. The actual deployment result depends on the native backend, quantized kernel support, ARM CPU behavior, memory access patterns, JNI integration, and device scheduling.

## 12. Final Recommendation

For the current ASR-Mobile Android deployment, the recommended model is:

```text
ggml-tiny.bin
```

Reasons:

- It is small enough for local phone deployment at about 74 MB.
- It achieved average RTF 0.822 on the Huawei phone, which is faster than real time.
- It produced usable Chinese transcription quality.
- It was more practical than the tested quantized variants in the current Android backend.

The quantized models should still be included in the report as compression experiments. They demonstrate clear size reduction and reveal the real trade-off between smaller files and actual mobile runtime performance.

## 13. Limitations

- The PC benchmark uses 9 short, clean audio files, so the results show trends rather than production-level accuracy.
- GPU-side distillation and pruning results do not directly represent Android CPU performance.
- The distillation experiment is small-scale pseudo-label distillation, not a full reproduction of Distil-Whisper.
- Pruning is unstructured magnitude pruning and does not reduce dense model size without sparse storage or sparse kernels.
- Formal Android benchmark currently covers one Android phone and one Chinese recording.
- Q4 models loaded successfully in Android validation, but `tiny-q4_0` and `base-q4_0` timed out during supplemental formal benchmark.
- `base-q5_1` loaded successfully in Android validation, but timed out during formal benchmark.
- CER/WER scoring is currently available for the Chinese formal recording only.

## 14. Future Work

- Expand the Android benchmark to English/French recordings and longer/noisier real microphone recordings.
- Add CER/WER-based quality scoring for English and French recordings.
- Convert the best distilled/pruned checkpoint to GGUF/GGML and test whether it remains compatible with whisper.cpp.
- Explore structured pruning or layer dropping, which may be more useful for dense mobile runtimes.
- Combine distillation with quantization-aware training for a stronger compression pipeline.
- Tune Android native backend settings, including thread count and ARM quantized kernel behavior.
- Add streaming ASR instead of full-file transcription.

## 15. References

- Whisper: https://arxiv.org/abs/2212.04356
- Distil-Whisper: https://arxiv.org/abs/2311.00430
- DQ-Whisper / Whisper-KDQ: https://arxiv.org/html/2305.10788v2
- CTranslate2 quantization: https://opennmt.net/CTranslate2/quantization.html
- CTranslate2 runtime optimizations: https://github.com/OpenNMT/CTranslate2
- Model compression survey: https://pmc.ncbi.nlm.nih.gov/articles/PMC11965593/
- Whisper pruning/adaptation reference: https://aclanthology.org/2023.mrl-1.7.pdf
