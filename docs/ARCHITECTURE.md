# Architecture

```text
User
  -> Android UI
  -> model file selection
  -> microphone recording
  -> 16 kHz mono WAV file
  -> Kotlin WhisperEngine
  -> JNI bridge
  -> native whisper.cpp runtime
  -> transcript and benchmark metrics
```

## Components

| Component | File | Responsibility |
|---|---|---|
| MainActivity | [../android/app/src/main/java/com/example/asrmobile/MainActivity.kt](../android/app/src/main/java/com/example/asrmobile/MainActivity.kt) | Simple UI and user flow |
| ModelFileManager | [../android/app/src/main/java/com/example/asrmobile/ModelFileManager.kt](../android/app/src/main/java/com/example/asrmobile/ModelFileManager.kt) | Copy selected model into app storage |
| AudioRecorder | [../android/app/src/main/java/com/example/asrmobile/AudioRecorder.kt](../android/app/src/main/java/com/example/asrmobile/AudioRecorder.kt) | Record 16 kHz mono PCM WAV |
| WhisperEngine | [../android/app/src/main/java/com/example/asrmobile/WhisperEngine.kt](../android/app/src/main/java/com/example/asrmobile/WhisperEngine.kt) | Kotlin wrapper around native ASR backend |
| BenchmarkRunner | [../android/app/src/main/java/com/example/asrmobile/BenchmarkRunner.kt](../android/app/src/main/java/com/example/asrmobile/BenchmarkRunner.kt) | Collect latency, RTF, memory, and device metrics |
| JNI bridge | [../android/app/src/main/cpp/whisper_jni.cpp](../android/app/src/main/cpp/whisper_jni.cpp) | Native C++ bridge to whisper.cpp |

## Offline-first design

The base app requests microphone permission only. It does not request internet permission, which supports local/offline ASR experiments.
