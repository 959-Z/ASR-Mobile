# Day 4 Benchmark Outputs

This folder stores formal Android benchmark CSV files exported from the ASR Mobile app.

## Expected Files

Per-model benchmark files:

```text
day4-Chinese-ggml-tiny.csv
day4-Chinese-ggml-tiny-q8_0.csv
day4-Chinese-ggml-tiny-q5_1.csv
day4-Chinese-ggml-base-q8_0.csv
day4-Chinese-ggml-base-q5_1.csv
day4-Chinese-ggml-base.csv
```

Models that time out may not produce a CSV. For those runs, keep the screenshot and UI XML evidence instead:

```text
day4-Chinese-ggml-tiny-q4_0-timeout-20260627-123556.png
day4-Chinese-ggml-tiny-q4_0-timeout-20260627-123556.xml
day4-Chinese-ggml-base-q4_0-timeout-20260627-124019.png
day4-Chinese-ggml-base-q4_0-timeout-20260627-124019.xml
day4-Chinese-ggml-base-q5_1-timeout-20260621-162436.png
day4-Chinese-ggml-base-q5_1-timeout-20260621-162436.xml
```

Generated summary files:

```text
day4-all-runs.csv
day4-model-summary.csv
day4-quality-analysis.csv
```

Generated chart files:

```text
day4-size-comparison.svg
day4-rtf-comparison.svg
```

## Recommended Commands

After recording a fresh 10-second Chinese audio clip in the app:

```bash
./scripts/run_day4_benchmark_matrix.sh com.example.asrmobile Chinese
python3 scripts/summarize_day4_benchmarks.py
python3 scripts/generate_day4_report_assets.py
```

For a quick smoke test with only one model:

```bash
./scripts/run_day4_benchmark_matrix.sh com.example.asrmobile Chinese ggml-tiny-q4_0.bin
```

## Report Metrics

Use `day4-model-summary.csv` for:

- model size comparison
- load time comparison
- average inference time comparison
- average RTF comparison
- memory delta comparison
- transcript quality inspection
- estimated CER and quality scoring
