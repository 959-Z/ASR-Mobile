#!/usr/bin/env bash
set -euo pipefail

PACKAGE_NAME="${1:-com.example.asrmobile}"
AUDIO_LANGUAGE="${2:-Chinese}"
MODEL_SELECTION="${3:-core}"
TIMEOUT_S="${4:-300}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="$ROOT_DIR/benchmarks/day4"
APP_MODEL_DIR="/data/user/0/$PACKAGE_NAME/files/models"

CORE_MODELS=(
  "ggml-tiny.bin"
  "ggml-tiny-q8_0.bin"
  "ggml-tiny-q5_1.bin"
  "ggml-base-q8_0.bin"
  "ggml-base-q5_1.bin"
)

FULL_MODELS=(
  "${CORE_MODELS[@]}"
  "ggml-tiny-q4_0.bin"
  "ggml-base-q4_0.bin"
  "ggml-base.bin"
)

case "$MODEL_SELECTION" in
  core)
    MODELS=("${CORE_MODELS[@]}")
    ;;
  full|all)
    MODELS=("${FULL_MODELS[@]}")
    ;;
  *)
    IFS=',' read -r -a MODELS <<< "$MODEL_SELECTION"
    ;;
esac

mkdir -p "$OUTPUT_DIR"

count_csv() {
  adb shell "run-as $PACKAGE_NAME sh -c 'ls files/benchmarks/benchmark-*.csv 2>/dev/null | wc -l'" | tr -d '\r[:space:]'
}

latest_csv() {
  adb shell "run-as $PACKAGE_NAME sh -c 'ls -t files/benchmarks/benchmark-*.csv 2>/dev/null | head -n 1'" | tr -d '\r'
}

wait_for_new_csv() {
  local before_count="$1"
  local timeout_s="${2:-300}"
  local start
  start="$(date +%s)"

  while true; do
    current_count="$(count_csv)"
    if [[ "$current_count" =~ ^[0-9]+$ ]] && (( current_count > before_count )); then
      return 0
    fi

    now="$(date +%s)"
    if (( now - start > timeout_s )); then
      echo "Timed out waiting for benchmark CSV" >&2
      return 1
    fi

    sleep 3
  done
}

adb shell svc power stayon usb >/dev/null

recording_check="$(adb shell "run-as $PACKAGE_NAME sh -c 'test -s files/recordings/latest.wav && echo ok || echo missing'" | tr -d '\r')"
if [[ "$recording_check" != "ok" ]]; then
  echo "No latest recording found in app storage. Record audio in the app first." >&2
  exit 1
fi

for model in "${MODELS[@]}"; do
  echo "Running benchmark for $model"
  before_count="$(count_csv)"
  adb shell am force-stop "$PACKAGE_NAME" >/dev/null
  adb shell am start -n "$PACKAGE_NAME/.MainActivity" \
    --es model_path "$APP_MODEL_DIR/$model" \
    --es model_name "$model" \
    --es audio_language "$AUDIO_LANGUAGE" \
    --ez auto_load true \
    --ez auto_benchmark true >/dev/null

  if ! wait_for_new_csv "$before_count" "$TIMEOUT_S"; then
    timestamp="$(date +%Y%m%d-%H%M%S)"
    safe_name="${model%.bin}"
    adb shell uiautomator dump /sdcard/window.xml >/dev/null || true
    adb exec-out cat /sdcard/window.xml > "$OUTPUT_DIR/day4-${AUDIO_LANGUAGE}-${safe_name}-timeout-${timestamp}.xml" || true
    adb exec-out screencap -p > "$OUTPUT_DIR/day4-${AUDIO_LANGUAGE}-${safe_name}-timeout-${timestamp}.png" || true
    adb shell am force-stop "$PACKAGE_NAME" >/dev/null || true
    echo "Timed out for $model; saved timeout UI evidence and continuing." >&2
    continue
  fi
  csv_path="$(latest_csv)"
  safe_name="${model%.bin}"
  output_file="$OUTPUT_DIR/day4-${AUDIO_LANGUAGE}-${safe_name}.csv"
  adb exec-out run-as "$PACKAGE_NAME" cat "$csv_path" > "$output_file"
  echo "Saved $output_file"
done

echo "Day 4 benchmark matrix complete: $OUTPUT_DIR"
