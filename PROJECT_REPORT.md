# ASR Mobile Project Report

## 1. Problem statement

This project studies how to deploy Automatic Speech Recognition (ASR) models on Android mobile devices. The target is local/on-device inference so that speech can be transcribed without sending audio to a cloud server.

## 2. Motivation

Mobile ASR is useful for note taking, accessibility, language learning, meeting transcription, and privacy-sensitive applications. Compared with server-side ASR, mobile deployment must balance accuracy, latency, memory, battery, model size, and device compatibility.

## 3. Related baseline

The course repository includes a desktop ASR script at [../machine_learning_2026_spring/session-402-audio-whisper-tts/whisper_audio_to_txt.py](../machine_learning_2026_spring/session-402-audio-whisper-tts/whisper_audio_to_txt.py). It uses `faster_whisper`, supports several Whisper model sizes, and can serve as a desktop quality/latency baseline.

For Android deployment, this project uses a native mobile direction based on `whisper.cpp`, because Python `faster_whisper` is not directly suitable for packaging into an Android app.

## 4. System architecture

```text
Android UI
  -> microphone recorder / selected WAV file
  -> local model file manager
  -> Kotlin WhisperEngine wrapper
  -> JNI native backend
  -> whisper.cpp runtime
  -> transcript and benchmark metrics
```

## 5. Mobile constraints

Key constraints to evaluate:

- Model size: affects APK/storage size and loading time.
- CPU performance: many phones do not have laptop-class CPU throughput.
- Memory: ASR models can exceed practical RAM budgets.
- Battery: long inference may drain battery.
- Latency: interactive ASR needs low real-time factor.
- Offline privacy: no internet permission is requested by the base app.
- Multilingual recognition: English, French, and Chinese should be tested if suitable models/audio are available.

## 6. Chosen deployment strategy

The runtime is `whisper.cpp` with GGML Whisper models. It is C/C++ based, works with Android NDK/JNI, and supports CPU-only inference.

The project evaluates both a baseline tiny model and quantized tiny/base variants. Quantization is used as the main compression method because it can reduce model size without retraining, which is practical for a short mobile deployment project.

## 7. Benchmark methodology

Measure:

- device model and Android version
- CPU ABI
- model filename and size
- audio duration
- model load time
- transcription time
- real-time factor = transcription time / audio duration
- approximate Java and native memory use
- transcript quality notes

Use [BENCHMARKING.md](BENCHMARKING.md) for the detailed procedure.

## 8. Formal Android benchmark results

Formal Chinese benchmark setup:

| Field | Value |
|---|---|
| Device | HUAWEI HBN-AL10 |
| Android | 12 |
| ABI | arm64-v8a |
| Audio | 10-second Chinese recording |
| Repetitions | 3 per model |

Results:

| Model | Quantization | Size MB | Load ms | Avg inference ms | Avg RTF | Result |
|---|---|---:|---:|---:|---:|---|
| `ggml-tiny.bin` | baseline | 74.09 | 400 | 8226.67 | 0.822 | success |
| `ggml-tiny-q8_0.bin` | Q8 | 41.52 | 251 | 40064.67 | 4.006 | success |
| `ggml-tiny-q4_0.bin` | Q4 | 24.15 | 127 in Day 2 loading validation | timeout | timeout | timeout |
| `ggml-tiny-q5_1.bin` | Q5 | 30.66 | 253 | 108814.67 | 10.882 | success |
| `ggml-base-q8_0.bin` | Q8 | 77.98 | 203 | 111234.33 | 11.123 | success |
| `ggml-base-q4_0.bin` | Q4 | 44.32 | 137 in Day 2 loading validation | timeout | timeout | timeout |
| `ggml-base-q5_1.bin` | Q5 | 56.94 | unknown | timeout | timeout | timeout |

The detailed results are stored in [benchmarks/day4/DAY4_CHINESE_FORMAL_SUMMARY.md](benchmarks/day4/DAY4_CHINESE_FORMAL_SUMMARY.md).

## 9. Analysis

The tiny quantized models reduced file size substantially:

| Model | Size MB | Size vs tiny baseline | Reduction |
|---|---:|---:|---:|
| `ggml-tiny.bin` | 74.09 | 100.00% | 0.00% |
| `ggml-tiny-q8_0.bin` | 41.52 | 56.04% | 43.96% |
| `ggml-tiny-q5_1.bin` | 30.66 | 41.38% | 58.62% |
| `ggml-tiny-q4_0.bin` | 24.15 | 32.60% | 67.40% |

However, quantization did not improve speed on the tested Huawei phone. The baseline `ggml-tiny.bin` was the only model with RTF < 1, meaning it completed transcription faster than real time. The quantized models were smaller but slower in this Android setup.

Recognition quality was evaluated with CER and WER against the Chinese reference sentence:

| Model | CER | WER | Quality score |
|---|---:|---:|---:|
| `ggml-tiny.bin` | 0.226 | 0.174 | 4/5 |
| `ggml-tiny-q8_0.bin` | 0.226 | 0.174 | 4/5 |
| `ggml-tiny-q5_1.bin` | 0.283 | 0.239 | 4/5 |
| `ggml-base-q8_0.bin` | 0.358 | 0.413 | 3/5 |

CER uses normalized character-level edit distance. WER uses a token sequence where Chinese characters are treated as individual tokens and English/numeric spans are treated as word tokens. The full scoring output is stored in [benchmarks/day4/day4-quality-analysis.csv](benchmarks/day4/day4-quality-analysis.csv).

This result is important because it shows that model compression does not automatically produce faster mobile inference. The actual deployment result depends on the native backend, quantized kernel support, ARM CPU behavior, memory access patterns, and device scheduling.

## 10. Final recommendation

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

## 11. Limitations

- Formal benchmark currently covers one Android phone and one Chinese recording.
- English and French formal runs are not completed yet.
- Streaming transcription is not implemented.
- Q4 models loaded successfully in Android validation, but `tiny-q4_0` and `base-q4_0` timed out during supplemental formal benchmark.
- `base-q5_1` loaded successfully in Android validation, but timed out during formal benchmark.
- CER/WER scoring is currently available for the Chinese formal recording only.

## 12. Future work

- Streaming ASR instead of full-file transcription.
- Voice activity detection before ASR.
- Noise reduction preprocessing.
- More complete English/French/Chinese benchmark set.
- CER/WER-based quality scoring for English and French recordings.
- Android native backend tuning, including thread count and ARM quantized kernel behavior.
- ONNX Runtime Mobile comparison.
- RAG or LLM post-processing for transcript correction and summarization.

## 13. References

- Whisper / Whisper model family
- whisper.cpp mobile inference runtime
- Android AudioRecord and Android NDK/JNI documentation
- The course Project.md requirements
