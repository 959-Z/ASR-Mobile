# Native Backend Placeholder

This directory contains the JNI bridge for the Android ASR backend.

## Current state

`whisper_jni.cpp` is a safe placeholder. It compiles a native library and returns a clear message that the `whisper.cpp` backend is not configured yet.

## Manual integration steps

1. Ask for approval before downloading third-party source.
2. Manually place `whisper.cpp` source under:

   ```text
   android/app/src/main/cpp/third_party/whisper.cpp/
   ```

3. Update `CMakeLists.txt` to build and link the whisper.cpp library.
4. Replace the TODO sections in `whisper_jni.cpp` with real model loading, transcription, and cleanup.
5. Provide a local model file manually. See [../../../../../../MODEL_SETUP.md](../../../../../../MODEL_SETUP.md).

This project does not download source code or model weights automatically.
