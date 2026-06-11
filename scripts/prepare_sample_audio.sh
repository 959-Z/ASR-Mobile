#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  printf 'Usage: %s <input-audio> <output-wav>\n' "$0" >&2
  printf 'Example: %s ./samples/input.m4a ./samples/input-16k-mono.wav\n' "$0" >&2
  exit 2
fi

INPUT="$1"
OUTPUT="$2"

if [ ! -f "$INPUT" ]; then
  printf 'Input audio not found: %s\n' "$INPUT" >&2
  printf 'This script does not download sample audio. Record or provide a local file.\n' >&2
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  printf 'ffmpeg is required for conversion but was not found in PATH.\n' >&2
  printf 'Install ffmpeg manually or export audio as 16 kHz mono WAV from another tool.\n' >&2
  exit 1
fi

ffmpeg -y -i "$INPUT" -ar 16000 -ac 1 -c:a pcm_s16le "$OUTPUT"
printf 'Created 16 kHz mono WAV: %s\n' "$OUTPUT"
