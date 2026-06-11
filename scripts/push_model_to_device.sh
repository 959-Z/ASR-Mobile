#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  printf 'Usage: %s <local-model-file> [application-id]\n' "$0" >&2
  printf 'Example: %s ./models/ggml-tiny.en.bin com.example.asrmobile\n' "$0" >&2
  exit 2
fi

MODEL_FILE="$1"
APP_ID="${2:-com.example.asrmobile}"
TARGET_DIR="/sdcard/Android/data/${APP_ID}/files/models"

if [ ! -f "$MODEL_FILE" ]; then
  printf 'Model file not found: %s\n' "$MODEL_FILE" >&2
  printf 'This script does not download models. Ask before downloading any model.\n' >&2
  exit 1
fi

case "$MODEL_FILE" in
  *.bin|*.gguf|*.ggml|*.onnx|*.tflite) ;;
  *)
    printf 'Warning: model file extension is not a common ASR deployment format. Continuing.\n' >&2
    ;;
esac

adb shell "mkdir -p '$TARGET_DIR'"
adb push "$MODEL_FILE" "$TARGET_DIR/"
printf 'Pushed model to %s/\n' "$TARGET_DIR"
