# Day 4 Android Benchmark Preparation

## Goal

Day 4 will run formal Android benchmarks on the Huawei phone using the quantized model matrix prepared by A and validated by B.

The benchmark should compare:

- model size
- load time
- inference time
- real-time factor
- Java/native heap delta
- recognition text quality

## Current Preparation Status

Completed before recording:

- A's model files were extracted into `models/`.
- All required tiny/base Q8/Q5/Q4 models were pushed to the phone.
- All required models were validated as loadable on Android.
- The app supports ADB-driven model selection.
- The app supports ADB-driven automatic benchmark after model loading.
- Day 4 scripts were prepared.
- A smoke test using the older `latest.wav` confirmed that automatic model loading, benchmark execution, CSV export, and summary generation work end to end.

## Model Matrix For Day 4

| Model file | Scale | Quantization | Android loading status |
|---|---|---|---|
| `ggml-tiny.bin` | tiny | baseline | validated earlier |
| `ggml-tiny-q8_0.bin` | tiny | Q8 | validated |
| `ggml-tiny-q5_1.bin` | tiny | Q5 | validated |
| `ggml-tiny-q4_0.bin` | tiny | Q4 | validated |
| `ggml-base.bin` | base | baseline | validated |
| `ggml-base-q8_0.bin` | base | Q8 | validated |
| `ggml-base-q5_1.bin` | base | Q5 | validated |
| `ggml-base-q4_0.bin` | base | Q4 | validated |

## Required Recording Work

Before running the formal benchmark matrix, record at least one fresh 10-second audio clip in the Android app.

Recommended Chinese script:

```text
这是 ASR Mobile 项目的第四天正式测试。我们正在比较不同量化模型在华为手机上的离线语音识别速度和识别质量。
```

Recommended English script:

```text
This is the fourth day benchmark for the ASR Mobile project. We are comparing quantized Whisper models on a Huawei Android phone.
```

Minimum acceptable setup:

- one Chinese 10-second recording

Better setup:

- one Chinese 10-second recording
- one English 10-second recording

## Scripts

Sync model files to the phone:

```bash
./scripts/sync_day4_models_to_device.sh
```

Run the Day 4 benchmark matrix for a Chinese recording:

```bash
./scripts/run_day4_benchmark_matrix.sh com.example.asrmobile Chinese core
```

Run the Day 4 benchmark matrix for an English recording:

```bash
./scripts/run_day4_benchmark_matrix.sh com.example.asrmobile English core
```

Run the full matrix, including aggressive Q4 variants and unquantized base:

```bash
./scripts/run_day4_benchmark_matrix.sh com.example.asrmobile Chinese full
```

Run one model only:

```bash
./scripts/run_day4_benchmark_matrix.sh com.example.asrmobile Chinese ggml-tiny-q8_0.bin
```

Generate summary CSV files:

```bash
python3 scripts/summarize_day4_benchmarks.py
```

## Recommended Benchmark Order

Start with the core matrix:

```text
ggml-tiny.bin
ggml-tiny-q8_0.bin
ggml-tiny-q5_1.bin
ggml-base-q8_0.bin
ggml-base-q5_1.bin
```

Then run the extended models if time allows:

```text
ggml-tiny-q4_0.bin
ggml-base-q4_0.bin
ggml-base.bin
```

This order is recommended because a smoke test showed that some quantized models can run much slower than expected on the phone. The result is still useful for the report: quantization reduces model size, but actual speed depends on backend kernel support and device behavior.

## Expected Output

The benchmark script exports one CSV per model into:

```text
evaluation/android_benchmarks/day4/
```

Each CSV contains three repeated runs for the same model and audio file.

Current files in this folder may include smoke-test outputs using the older Day 1 recording. After the fresh Day 4 recording is made, rerun the benchmark script and regenerate the summary files.

## Important Path Note

Use the app private model path for formal benchmarks:

```text
/data/user/0/com.example.asrmobile/files/models/<model-file>
```

Do not use the external Android data path for formal results:

```text
/sdcard/Android/data/com.example.asrmobile/files/models/<model-file>
```

At least one model failed to load from the external path, while the private app path worked.

## Acceptance Checklist

- [ ] Fresh recording exists as `files/recordings/latest.wav`.
- [ ] All Day 4 model files exist on the phone.
- [ ] Each model produces a CSV file.
- [ ] Each CSV contains 3 benchmark rows.
- [ ] CSV fields include model name, quantization, language, model size, load time, inference time, RTF, memory delta, transcript, quality score, and notes.
- [ ] Results are copied into `evaluation/android_benchmarks/day4/`.
