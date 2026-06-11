# Benchmarking

This project evaluates Android on-device ASR deployment using latency, memory, model size, and recognition quality.

## Metrics

| Metric | Meaning |
|---|---|
| Model size | Local model file size in MB |
| Load time | Time to initialize the ASR model |
| Audio duration | Length of test speech input |
| Inference time | Wall-clock transcription time |
| Real-time factor (RTF) | inference time / audio duration; lower is better |
| Java heap | Approximate Java heap use before/after inference |
| Native heap | Approximate native heap allocation |
| Transcript quality | Manual notes or WER if reference text is available |

## Recommended test cases

Use short samples first:

- 5 seconds English
- 15 seconds English
- 15 seconds French
- 15 seconds Chinese
- 30 seconds mixed/noisy sample if available

## Benchmark table

| Device | Android | ABI | Model | Model size | Language | Audio duration | Load time | Inference time | RTF | Memory notes | Transcript notes |
|---|---|---|---|---:|---|---:|---:|---:|---:|---|---|
| TBD | TBD | TBD | TBD | TBD | English | TBD | TBD | TBD | TBD | TBD | TBD |
| TBD | TBD | TBD | TBD | TBD | French | TBD | TBD | TBD | TBD | TBD | TBD |
| TBD | TBD | TBD | TBD | TBD | Chinese | TBD | TBD | TBD | TBD | TBD | TBD |

## Offline verification

To demonstrate local deployment:

1. Install the app.
2. Put the device in airplane mode.
3. Load a local model file.
4. Record or select local audio.
5. Transcribe successfully without network access.

The base app does not request Android internet permission.
