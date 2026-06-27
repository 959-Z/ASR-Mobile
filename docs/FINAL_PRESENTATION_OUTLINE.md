# Final Presentation Outline

## 1. Project Goal

Explain that ASR-Mobile is an Android offline ASR deployment project, not only a model compression experiment.

Key sentence:

```text
Our goal is to verify whether Whisper-based ASR can run locally on an Android phone and evaluate the deployment trade-off between model size, speed, memory, and recognition quality.
```

## 2. System Architecture

Show the chain:

```text
Android UI -> Recording -> WAV -> Kotlin WhisperEngine -> JNI -> whisper.cpp -> Transcript + Benchmark CSV
```

Mention:

- local recording
- local model file
- offline inference
- benchmark export

## 3. Division Of Work

| Role | Work |
|---|---|
| A | Model collection, quantized model matrix, model size and quantization theory |
| B | Android app, benchmark pipeline, phone testing, result analysis |

## 4. Model Matrix

Discuss:

- tiny baseline
- tiny Q8/Q5/Q4
- base baseline
- base Q8/Q5/Q4

Explain Q8/Q5/Q4:

- Q8: conservative compression
- Q5: balanced compression
- Q4: aggressive compression

## 5. Benchmark Method

Mention:

- HUAWEI HBN-AL10
- Android 12
- arm64-v8a
- 10-second Chinese recording
- 3 repeated runs per model
- metrics: model size, load time, inference time, RTF, memory, transcript

## 6. Results

Use this table:

| Model | Size MB | Avg RTF | Result |
|---|---:|---:|---|
| `ggml-tiny.bin` | 74.09 | 0.822 | best practical model |
| `ggml-tiny-q8_0.bin` | 41.52 | 4.006 | smaller but slower |
| `ggml-tiny-q4_0.bin` | 24.15 | timeout | loaded, then timed out |
| `ggml-tiny-q5_1.bin` | 30.66 | 10.882 | much smaller but too slow |
| `ggml-base-q8_0.bin` | 77.98 | 11.123 | completed but not practical |
| `ggml-base-q4_0.bin` | 44.32 | timeout | loaded, then timed out |
| `ggml-base-q5_1.bin` | 56.94 | timeout | timed out |

Suggested figures:

- `model_benchmark/method_comparison.png`
- `model_benchmark/pruning_tradeoff.png`
- `model_benchmark/accuracy_comparison.png`
- `model_benchmark/speed_comparison.png`
- `model_benchmark/resource_comparison.png`
- `benchmarks/day4/day4-size-comparison.svg`
- `benchmarks/day4/day4-rtf-comparison.svg`

Quality table:

| Model | CER | WER | Quality score |
|---|---:|---:|---:|
| `ggml-tiny.bin` | 0.226 | 0.174 | 4/5 |
| `ggml-tiny-q8_0.bin` | 0.226 | 0.174 | 4/5 |
| `ggml-tiny-q5_1.bin` | 0.283 | 0.239 | 4/5 |
| `ggml-base-q8_0.bin` | 0.358 | 0.413 | 3/5 |

## 7. Key Finding

Main finding:

```text
Quantization reduced model size, but did not improve speed on our Android backend.
```

Explain why:

- quantized kernels may not be optimized for this device/backend
- CPU memory access and thread scheduling matter
- mobile deployment must be measured on real hardware

## 8. Final Recommendation

Recommend:

```text
ggml-tiny.bin
```

Reason:

- RTF < 1
- small enough for phone storage
- usable Chinese transcription
- most stable in the experiment

## 9. Limitations

- only one phone tested
- only Chinese formal run completed
- CER/WER currently covers Chinese only
- no streaming ASR
- Q4 loaded successfully but timed out in supplemental formal benchmark

## 10. Future Work

- English/French formal benchmark
- CER/WER scoring for English/French recordings
- voice activity detection
- streaming ASR
- ARM backend and thread optimization
- post-processing correction
