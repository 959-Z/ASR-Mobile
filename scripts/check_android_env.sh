#!/usr/bin/env bash
set -euo pipefail

printf 'ASR Mobile Android environment check\n'
printf '====================================\n'

status=0

require_command() {
  local name="$1"
  local install_hint="$2"
  if command -v "$name" >/dev/null 2>&1; then
    return 0
  fi

  printf '%s: not found. %s\n' "$name" "$install_hint"
  status=1
  return 1
}

if command -v java >/dev/null 2>&1; then
  java -version
  java_version=$(java -version 2>&1 | awk -F '"' '/version/ { print $2; exit }')
  java_major=$(printf '%s' "$java_version" | awk -F. '{ if ($1 == "1") print $2; else print $1 }')
  if [ "${java_major:-0}" -lt 17 ]; then
    printf 'java: version %s detected, but Android Gradle Plugin 8.x needs JDK 17 or newer.\n' "$java_version"
    status=1
  fi
else
  printf 'java: not found. Install JDK 17 or use Android Studio bundled JDK.\n'
  status=1
fi

require_command adb 'Install Android SDK platform-tools.' && adb version
require_command cmake 'Android Studio can install/use its bundled CMake.' && cmake --version | head -n 1

if [ -n "${ANDROID_HOME:-}" ]; then
  printf 'ANDROID_HOME=%s\n' "$ANDROID_HOME"
elif [ -n "${ANDROID_SDK_ROOT:-}" ]; then
  printf 'ANDROID_SDK_ROOT=%s\n' "$ANDROID_SDK_ROOT"
else
  printf 'ANDROID_HOME is not set. Android Studio may still manage SDK paths locally.\n'
  status=1
fi

if [ -f android/gradlew ] || [ -f android/gradlew.bat ]; then
  printf 'Gradle wrapper: found in android/.\n'
elif command -v gradle >/dev/null 2>&1; then
  printf 'Gradle: found on PATH. Consider generating a project wrapper later.\n'
else
  printf 'Gradle wrapper: not found. Open android/ in Android Studio first, or install Gradle to generate ./gradlew.\n'
  status=1
fi

if [ -d android/app/src/main/cpp/third_party/whisper.cpp ]; then
  printf 'whisper.cpp source: found.\n'
else
  printf 'whisper.cpp source: missing at android/app/src/main/cpp/third_party/whisper.cpp.\n'
  status=1
fi

if ls models/*.bin >/dev/null 2>&1; then
  printf 'Local whisper.cpp model files:\n'
  ls -lh models/*.bin
else
  printf 'Local whisper.cpp model file: none found in models/.\n'
fi

printf '\nThis script only checks tools. It does not install or download models.\n'
exit "$status"
