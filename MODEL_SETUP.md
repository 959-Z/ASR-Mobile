# Model Setup

## No automatic model download policy

This project intentionally does **not** download ASR model weights.

- Do not add scripts that run `wget`, `curl`, `git clone`, or Hugging Face download commands for model weights without approval.
- Do not commit model binaries to Git.
- If model download is needed, ask the project owner first.

## Recommended model family

For Android on-device ASR, start with a small whisper.cpp-compatible quantized Whisper model, for example:

- `ggml-tiny.en.bin` for the fastest English-only demo
- `ggml-base.en.bin` for better English quality
- multilingual tiny/base models for English, French, and Chinese experiments

Large models are usually too slow and too large for a first Android demo.

## Local model folder

Put user-provided model files in:

```text
ASR Mobile/models/
```

This folder is ignored by Git except for its `README.md` placeholder.

## Android placement options

### Option 1: select model from Android storage

The recommended workflow is to copy the model to the phone manually and select it from the app UI.

### Option 2: push with adb

Use the helper script with a local model path:

```bash
./scripts/push_model_to_device.sh ./models/ggml-tiny.en.bin com.example.asrmobile
```

The script requires an existing local file and does not download anything.

### Option 3: Android assets for a controlled demo

For a one-file demo APK, place a small model in:

```text
android/app/src/main/assets/models/ggml-tiny.bin
```

Then rebuild the APK. The app shows a **Use bundled tiny model** button that copies this asset into app-private storage and selects it for loading.

This simplifies demos but increases APK size. Model files in that directory are ignored by Git by default.

## Suggested experiment matrix

| Model | Language | File size | Device | Audio length | Inference time | RTF | Notes |
|---|---|---:|---|---:|---:|---:|---|
| tiny | English | TBD | TBD | 5 s | TBD | TBD | baseline |
| base | English | TBD | TBD | 15 s | TBD | TBD | quality comparison |
| tiny multilingual | French/Chinese | TBD | TBD | 15 s | TBD | TBD | multilingual test |
