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

## 6. Quantization Experiment

The quantization experiment tested 8 GGML models on 9 short audio files across English, Chinese, and French.

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

The strongest low-resource Android candidate is `ggml-tiny-q4_0.bin`: it is only 24.15 MB and has RTF 0.27 on the PC benchmark. The strongest quality candidate is `ggml-base-q4_0.bin`: it reaches 98.4% average accuracy in this short benchmark while being much smaller than the base baseline.

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

## 8. Engineering Decision

The project keeps GGML quantization as the Android deployment mainline because it is directly supported by whisper.cpp and can be loaded by the current native Android pipeline. Distillation and pruning are valuable research extensions, but they require additional conversion and runtime validation before they can become Android candidates.

Recommended Android validation order:

1. `ggml-tiny-q4_0.bin`
2. `ggml-base-q4_0.bin`
3. `ggml-base-q8_0.bin`
4. `ggml-tiny-q8_0.bin`

## 9. Limitations

- The PC benchmark uses 9 short, clean audio files, so the results show trends rather than production-level accuracy.
- GPU-side distillation and pruning results do not directly represent Android CPU performance.
- The distillation experiment is small-scale pseudo-label distillation, not a full reproduction of Distil-Whisper.
- Pruning is unstructured magnitude pruning and does not reduce dense model size without sparse storage or sparse kernels.
- Android real-device validation is still required for load time, memory, thermal behavior, and JNI/native stability.

## 10. Future Work

- Run Android-side benchmark for the recommended quantized models.
- Expand the audio benchmark to longer, noisy, and real microphone recordings.
- Convert the best distilled/pruned checkpoint to GGUF/GGML and test whether it remains compatible with whisper.cpp.
- Explore structured pruning or layer dropping, which may be more useful for dense mobile runtimes.
- Combine distillation with quantization-aware training for a stronger compression pipeline.

## 11. References

- Whisper: https://arxiv.org/abs/2212.04356
- Distil-Whisper: https://arxiv.org/abs/2311.00430
- DQ-Whisper / Whisper-KDQ: https://arxiv.org/html/2305.10788v2
- CTranslate2 quantization: https://opennmt.net/CTranslate2/quantization.html
- CTranslate2 runtime optimizations: https://github.com/OpenNMT/CTranslate2
- Model compression survey: https://pmc.ncbi.nlm.nih.gov/articles/PMC11965593/
- Whisper pruning/adaptation reference: https://aclanthology.org/2023.mrl-1.7.pdf
