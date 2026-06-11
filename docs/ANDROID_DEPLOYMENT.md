# Android Deployment

## Environment

Recommended tools:

- Android Studio
- JDK 17 or Android Studio bundled JBR
- Android SDK Platform 35
- Android SDK Build Tools
- Android SDK Platform Tools (`adb`)
- Android NDK
- CMake 3.22.1 or newer
- A physical Android phone for realistic benchmarking

Run the read-only helper from the project root:

```bash
cd "ASR Mobile"
bash scripts/check_android_env.sh
```

On Windows, Android Studio usually installs the SDK under:

```text
%LOCALAPPDATA%\Android\Sdk
```

After installation, set these environment variables if command-line builds cannot find the SDK:

```bash
export ANDROID_HOME="$LOCALAPPDATA/Android/Sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$ANDROID_HOME/platform-tools:$PATH"
```

Current known project assets:

- `whisper.cpp` source should exist at `android/app/src/main/cpp/third_party/whisper.cpp/`.
- A local model can exist at `models/ggml-tiny.bin`; model binaries are ignored by Git.
- This project does not download model weights automatically.

## Build

Open [../android/](../android/) in Android Studio and build the app.

If a Gradle wrapper is later added, build from the command line:

```bash
cd android
./gradlew assembleDebug
```

## Run on device

1. Enable developer mode and USB debugging on the Android phone.
2. Connect the phone.
3. Build and install from Android Studio.
4. Grant microphone permission.
5. Select a local model file.
6. Record audio and transcribe.

## Offline demo

1. Put the device in airplane mode.
2. Confirm the app still opens.
3. Select a local model.
4. Record and transcribe.

This demonstrates local inference if the native backend and model are configured.
