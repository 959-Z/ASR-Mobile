# ONNX Runtime Mobile Alternative

ONNX Runtime Mobile is a possible alternative to `whisper.cpp`, especially if the team wants to compare mobile runtimes.

## Potential benefits

- Standard model exchange format
- Android Java/Kotlin APIs
- Good support for many neural network models

## Challenges for ASR

- Whisper export and decoding are more complex than simple classification models.
- Tokenizer, mel spectrogram, encoder, decoder loop, and postprocessing must be handled carefully.
- Operator support and binary size can require tuning.
- End-to-end Android implementation may take longer than whisper.cpp.

## Suggested use

Treat ONNX Runtime Mobile as an optional comparison after the whisper.cpp baseline works.

Possible comparison dimensions:

| Runtime | Model | APK size | Model size | Load time | RTF | Notes |
|---|---|---:|---:|---:|---:|---|
| whisper.cpp | tiny/base quantized | TBD | TBD | TBD | TBD | baseline |
| ONNX Runtime Mobile | exported ASR model | TBD | TBD | TBD | TBD | optional |
