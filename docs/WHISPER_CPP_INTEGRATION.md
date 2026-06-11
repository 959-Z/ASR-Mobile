# whisper.cpp Integration

The project uses `whisper.cpp` as the Android on-device ASR runtime.

## Why whisper.cpp?

- Native C/C++ implementation
- Android NDK compatible
- Quantized model support
- CPU-only inference path
- Good fit for edge/mobile experiments

## Current state

`whisper.cpp` source has been downloaded into:

```text
android/app/src/main/cpp/third_party/whisper.cpp/
```

The Android CMake file links the native app library against `whisper.cpp`, and [../android/app/src/main/cpp/whisper_jni.cpp](../android/app/src/main/cpp/whisper_jni.cpp) now implements:

- model loading with `whisper_init_from_file_with_params`
- 16 kHz 16-bit PCM WAV parsing
- mono float PCM conversion
- transcription with `whisper_full`
- transcript collection from generated segments
- context cleanup with `whisper_free`

## Supported input format

The native bridge currently supports:

- RIFF/WAVE
- 16-bit PCM
- 16 kHz sample rate
- mono or multi-channel input, mixed down to mono

The Android recorder writes 16 kHz mono WAV, so recordings made in the app are compatible.

## Model notes

A multilingual tiny model has been downloaded to [../models/ggml-tiny.bin](../models/ggml-tiny.bin). Model files remain ignored by Git. See [MODEL_SETUP.md](../MODEL_SETUP.md) and [MODEL_DOWNLOAD_STATUS.md](MODEL_DOWNLOAD_STATUS.md).
