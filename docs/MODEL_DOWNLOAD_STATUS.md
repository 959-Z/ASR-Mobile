# Model Download Status

`whisper.cpp` source code has been downloaded into:

```text
android/app/src/main/cpp/third_party/whisper.cpp/
```

The official Hugging Face URL timed out from this environment:

```text
https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin
```

A retry through the Hugging Face mirror succeeded:

```text
https://hf-mirror.com/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin
```

Downloaded model:

```text
ASR Mobile/models/ggml-tiny.bin
```

File size:

```text
77,691,713 bytes
```

This `tiny` model is multilingual and suitable for initial English/French/Chinese experiments, although accuracy is lower than larger models.

## Push model to Android device

After installing the Android app and connecting a device with USB debugging enabled:

```bash
cd "ASR Mobile"
./scripts/push_model_to_device.sh ./models/ggml-tiny.bin com.example.asrmobile
```

You can also manually copy the model to the phone and select it from the app UI.
