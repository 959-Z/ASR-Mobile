# ASR-Mobile Final Delivery Review

## Project Core Goal

ASR-Mobile is an Android offline speech recognition deployment project. The project goal is to run ASR locally on a phone through this system chain:

```text
Android UI -> recording -> WAV file -> Kotlin WhisperEngine -> JNI -> whisper.cpp -> transcript and benchmark metrics
```

The quantization and compression work serves this larger goal: finding a practical model choice for mobile deployment under model size, runtime speed, memory, and quality constraints.

## Completed Work

### Day 1: Baseline

- Huawei phone was connected and verified.
- Baseline recording was created and processed.
- `ggml-tiny.bin` baseline was tested on Android.
- Baseline metrics were recorded in `benchmarks/DAY1_BASELINE_SUMMARY.md`.

### Day 2: Model Preparation And Loading Validation

- A's model package was inspected.
- Missing model files were extracted into `models/`.
- Tiny/base Q8/Q5/Q4 variants were prepared for Android experiments.
- Android loading validation was completed.
- Validation results were recorded in `docs/DAY2_ANDROID_MODEL_VALIDATION.md`.

### Day 3: Android Benchmark Improvements

- Benchmark CSV fields were expanded.
- Model name, quantization level, audio language, model size, load time, inference time, RTF, heap deltas, transcript, quality score, and notes are now supported.
- Repeated benchmark runs were added.
- UI progress visualization and experiment summary were added.
- ADB automation support was added for model selection and automatic benchmark.

### Day 4: Formal Android Experiment

- Formal Chinese benchmark was completed on HUAWEI HBN-AL10.
- Four models completed formal benchmark successfully.
- `tiny-q4_0`, `base-q4_0`, and `base-q5_1` timed out and timeout evidence was saved.
- Summary CSV files were generated.
- Formal summary was written in `evaluation/android_benchmarks/day4/DAY4_CHINESE_FORMAL_SUMMARY.md`.

### Day 5: Analysis And Report Material

- `PROJECT_REPORT.md` was updated with real benchmark results.
- Final recommendation was written.
- Report charts were generated for model size and RTF comparison.
- CER/WER recognition quality analysis was generated.
- Remaining limitations and future work were clarified.
- This final delivery review was created.

## Main Experimental Result

| Model | Quantization | Size MB | Avg inference ms | Avg RTF | Result |
|---|---|---:|---:|---:|---|
| `ggml-tiny.bin` | baseline | 74.09 | 8226.67 | 0.822 | success |
| `ggml-tiny-q8_0.bin` | Q8 | 41.52 | 40064.67 | 4.006 | success |
| `ggml-tiny-q4_0.bin` | Q4 | 24.15 | timeout | timeout | timeout |
| `ggml-tiny-q5_1.bin` | Q5 | 30.66 | 108814.67 | 10.882 | success |
| `ggml-base-q8_0.bin` | Q8 | 77.98 | 111234.33 | 11.123 | success |
| `ggml-base-q4_0.bin` | Q4 | 44.32 | timeout | timeout | timeout |
| `ggml-base-q5_1.bin` | Q5 | 56.94 | timeout | timeout | timeout |

## Recognition Quality Result

| Model | CER | WER | Quality score |
|---|---:|---:|---:|
| `ggml-tiny.bin` | 0.226 | 0.174 | 4/5 |
| `ggml-tiny-q8_0.bin` | 0.226 | 0.174 | 4/5 |
| `ggml-tiny-q5_1.bin` | 0.283 | 0.239 | 4/5 |
| `ggml-base-q8_0.bin` | 0.358 | 0.413 | 3/5 |

The scoring output is stored in `evaluation/android_benchmarks/day4/day4-quality-analysis.csv`. CER uses normalized character edit distance; WER uses Chinese-character and English-word token edit distance.

## Final Recommendation

The recommended deployment model for the current Android setup is:

```text
ggml-tiny.bin
```

Reason:

- It is the only tested model with RTF < 1.
- It is small enough for practical phone-side deployment.
- It produced usable Chinese recognition output.
- Quantized models reduced file size but were much slower on this phone/backend combination.

## Course Knowledge Connection

| Course topic | Project evidence |
|---|---|
| Model evaluation | Benchmarked size, load time, inference time, RTF, memory, CER, WER, and transcript quality |
| Quantization | Compared Q8/Q5/Q4 variants against baseline models |
| Compression trade-off | Quantized models were smaller but slower in this Android backend |
| Lightweight architecture | Compared tiny and base model families |
| Edge deployment | Ran offline ASR on an Android phone using JNI and whisper.cpp |
| Reproducibility | Added CSV export, repeated runs, scripts, and documented test setup |

## Presentation Figures

Recommended figures for the report or PPT:

- `evaluation/pc_benchmark/method_comparison.png`
- `evaluation/pc_benchmark/pruning_tradeoff.png`
- `evaluation/pc_benchmark/accuracy_comparison.png`
- `evaluation/pc_benchmark/speed_comparison.png`
- `evaluation/pc_benchmark/resource_comparison.png`
- `evaluation/android_benchmarks/day4/day4-size-comparison.svg`
- `evaluation/android_benchmarks/day4/day4-rtf-comparison.svg`

## Remaining Tasks

The remaining tasks require project/team decisions rather than more local automation work:

- Record English audio if multilingual comparison is required.
- Decide whether to include English/French experiments in the final submission.
- Decide whether to push large model files to the remote repository.
- Confirm final report wording with teammate A.

## Delivery Files

Key files for final reporting:

- `PROJECT_REPORT.md`
- `docs/FINAL_DELIVERY_REVIEW.md`
- `docs/QUANTIZATION_COMPRESSION_WORK_PLAN.md`
- `docs/DAY2_ANDROID_MODEL_VALIDATION.md`
- `docs/DAY4_BENCHMARK_PREPARATION.md`
- `evaluation/android_benchmarks/day4/DAY4_CHINESE_FORMAL_SUMMARY.md`
- `evaluation/android_benchmarks/day4/day4-model-summary.csv`
- `evaluation/android_benchmarks/day4/day4-all-runs.csv`
- `evaluation/android_benchmarks/day4/day4-quality-analysis.csv`
- `evaluation/android_benchmarks/day4/day4-size-comparison.svg`
- `evaluation/android_benchmarks/day4/day4-rtf-comparison.svg`

## Important Caveat

This project should not claim that quantization always accelerates mobile inference. The actual measured result is more nuanced:

```text
Quantization reduced model size, but the tested quantized models were slower on this Android whisper.cpp setup.
```

This is a strong and honest deployment conclusion because it is based on real device measurements.
