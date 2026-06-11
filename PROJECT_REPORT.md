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

The recommended runtime is `whisper.cpp` with quantized Whisper models. It is C/C++ based, works with Android NDK/JNI, and supports CPU-only inference.

No model weights are bundled or downloaded automatically. See [MODEL_SETUP.md](MODEL_SETUP.md).

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

## 8. Planned results table

| Device | Android | ABI | Model | Audio | Duration | Load time | Inference time | RTF | Quality notes |
|---|---|---|---|---|---:|---:|---:|---:|---|
| TBD | TBD | arm64-v8a | tiny/base | English | TBD | TBD | TBD | TBD | TBD |
| TBD | TBD | arm64-v8a | tiny/base | French | TBD | TBD | TBD | TBD | TBD |
| TBD | TBD | arm64-v8a | tiny/base | Chinese | TBD | TBD | TBD | TBD | TBD |

## 9. Limitations

- The scaffold does not include model weights.
- The native backend requires manual `whisper.cpp` source placement.
- Streaming transcription is not implemented in the initial scaffold.
- Quantized small models may trade recognition quality for mobile speed.

## 10. Future work

- Streaming ASR instead of full-file transcription.
- Voice activity detection before ASR.
- Noise reduction preprocessing.
- More complete English/French/Chinese benchmark set.
- ONNX Runtime Mobile comparison.
- RAG or LLM post-processing for transcript correction and summarization.

## 11. References

- Whisper / Whisper model family
- whisper.cpp mobile inference runtime
- Android AudioRecord and Android NDK/JNI documentation
- The course Project.md requirements
