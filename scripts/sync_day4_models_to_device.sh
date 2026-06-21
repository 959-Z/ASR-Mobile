#!/usr/bin/env bash
set -euo pipefail

PACKAGE_NAME="${1:-com.example.asrmobile}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="$ROOT_DIR/models"
DEVICE_TMP_DIR="/data/local/tmp/asr-mobile-models"
APP_MODEL_DIR="/data/user/0/$PACKAGE_NAME/files/models"

MODELS=(
  "ggml-tiny.bin"
  "ggml-tiny-q8_0.bin"
  "ggml-tiny-q5_1.bin"
  "ggml-tiny-q4_0.bin"
  "ggml-base.bin"
  "ggml-base-q8_0.bin"
  "ggml-base-q5_1.bin"
  "ggml-base-q4_0.bin"
)

adb shell mkdir -p "$DEVICE_TMP_DIR"
adb shell run-as "$PACKAGE_NAME" mkdir -p "$APP_MODEL_DIR"

for model in "${MODELS[@]}"; do
  local_path="$MODELS_DIR/$model"
  if [[ ! -f "$local_path" ]]; then
    echo "Missing model: $local_path" >&2
    exit 1
  fi

  echo "Syncing $model"
  adb push "$local_path" "$DEVICE_TMP_DIR/$model" >/dev/null
  adb shell run-as "$PACKAGE_NAME" cp "$DEVICE_TMP_DIR/$model" "$APP_MODEL_DIR/$model"
done

adb shell run-as "$PACKAGE_NAME" ls -lh "$APP_MODEL_DIR"
