# Day 4 Chinese Formal Benchmark Summary

## Test Setup

| Field | Value |
|---|---|
| Date | 2026-06-21; Q4 timeout supplement on 2026-06-27 |
| Device | HUAWEI HBN-AL10 |
| Android version | 12 |
| ABI | arm64-v8a |
| Audio file | `latest.wav` |
| Audio duration | 10.00 s |
| Audio language | Chinese |
| Repetitions | 3 per model |

Reference text:

```text
这是 ASR Mobile 项目的第四天正式测试。我们正在比较不同量化模型在华为手机上的离线语音识别速度和识别质量。
```

## Completed Results

| Model | Quantization | Size MB | Load ms | Avg inference ms | Avg RTF | Speed vs tiny baseline | Result |
|---|---|---:|---:|---:|---:|---:|---|
| `ggml-tiny.bin` | baseline | 74.09 | 400 | 8226.67 | 0.822 | 1.00x | success |
| `ggml-tiny-q8_0.bin` | Q8 | 41.52 | 251 | 40064.67 | 4.006 | 4.87x slower | success |
| `ggml-tiny-q4_0.bin` | Q4 | 24.15 | 127 in Day 2 loading validation | timeout | timeout | timeout | timeout |
| `ggml-tiny-q5_1.bin` | Q5 | 30.66 | 253 | 108814.67 | 10.882 | 13.23x slower | success |
| `ggml-base-q8_0.bin` | Q8 | 77.98 | 203 | 111234.33 | 11.123 | 13.52x slower | success |
| `ggml-base-q4_0.bin` | Q4 | 44.32 | 137 in Day 2 loading validation | timeout | timeout | timeout | timeout |
| `ggml-base-q5_1.bin` | Q5 | 56.94 | unknown | timeout | timeout | timeout | timeout |

## Size Reduction

Using `ggml-tiny.bin` as the tiny baseline:

| Model | Size MB | Size vs tiny baseline | Reduction vs tiny baseline |
|---|---:|---:|---:|
| `ggml-tiny.bin` | 74.09 | 100.00% | 0.00% |
| `ggml-tiny-q8_0.bin` | 41.52 | 56.04% | 43.96% |
| `ggml-tiny-q5_1.bin` | 30.66 | 41.38% | 58.62% |
| `ggml-tiny-q4_0.bin` | 24.15 | 32.60% | 67.40% |

Using `ggml-base.bin` as the base baseline from A's model matrix:

| Model | Size MB | Size vs base baseline | Reduction vs base baseline |
|---|---:|---:|---:|
| `ggml-base.bin` | 141.10 | 100.00% | 0.00% |
| `ggml-base-q8_0.bin` | 77.98 | 55.27% | 44.73% |
| `ggml-base-q5_1.bin` | 56.94 | 40.35% | 59.65% |
| `ggml-base-q4_0.bin` | 44.32 | 31.41% | 68.59% |

## Recognition Quality Notes

The tiny baseline remained the most practical result in this formal Chinese run. It achieved RTF < 1, meaning it was faster than real time on the Huawei phone.

Recognition quality was scored with CER and WER against the reference sentence. CER uses normalized character-level edit distance. WER uses a token sequence where Chinese characters are treated as individual tokens and English/numeric spans are treated as word tokens.

| Model | CER | WER | Quality score | Note |
|---|---:|---:|---:|---|
| `ggml-tiny.bin` | 0.226 | 0.174 | 4/5 | usable, visible character errors |
| `ggml-tiny-q8_0.bin` | 0.226 | 0.174 | 4/5 | similar quality to tiny baseline, much slower |
| `ggml-tiny-q5_1.bin` | 0.283 | 0.239 | 4/5 | usable but more character errors |
| `ggml-base-q8_0.bin` | 0.358 | 0.413 | 3/5 | semantically recognizable, script/style mismatch appears |

The detailed scoring output is stored in `day4-quality-analysis.csv`.

All successful models recognized the rough content of the sentence, but there were visible transcription errors:

- `ASR Mobile` was often recognized as similar-sounding but incorrect text.
- `语音识别` was sometimes recognized as incorrect characters.
- Quantized tiny Q8 and Q5 produced similar semantic content but with worse speed.
- `base-q8_0` produced a more standard Chinese-looking transcript in some parts, but the runtime cost was too high for practical mobile use in this setup.

## Main Findings

1. Quantization strongly reduced model size.
2. On this Android whisper.cpp setup, quantized models did not improve speed.
3. Tiny baseline was the only model in this run with RTF < 1.
4. Tiny Q8 and Q5 were smaller but much slower than tiny baseline.
5. Base Q8 loaded successfully and completed benchmark, but its RTF was much larger than 1.
6. Tiny Q4 and base Q4 loaded successfully in Day 2 validation, but timed out during the supplemental formal benchmark.
7. Base Q5 loaded successfully in Day 2 validation, but timed out during formal Day 4 benchmark.

## Report Conclusion

For the current ASR-Mobile Android deployment, the best practical model from this Chinese benchmark is:

```text
ggml-tiny.bin
```

Reason:

- It is already small enough for phone-side deployment at 74.09 MB.
- It completed transcription faster than real time with average RTF 0.822.
- It produced usable Chinese transcription quality.
- It was much faster than the tested quantized variants on this Android backend.

The quantized models remain useful for the course report because they clearly demonstrate the trade-off between model size and real device performance. The result shows that compression does not automatically guarantee faster mobile inference; backend implementation, quantized kernel support, and device runtime behavior are decisive.

## Output Files

Successful benchmark CSV files:

- `day4-Chinese-ggml-tiny.csv`
- `day4-Chinese-ggml-tiny-q8_0.csv`
- `day4-Chinese-ggml-tiny-q5_1.csv`
- `day4-Chinese-ggml-base-q8_0.csv`

Timeout evidence:

- `day4-Chinese-ggml-base-q5_1-timeout-20260621-162436.png`
- `day4-Chinese-ggml-base-q5_1-timeout-20260621-162436.xml`
- `day4-Chinese-ggml-tiny-q4_0-timeout-20260627-123556.png`
- `day4-Chinese-ggml-tiny-q4_0-timeout-20260627-123556.xml`
- `day4-Chinese-ggml-base-q4_0-timeout-20260627-124019.png`
- `day4-Chinese-ggml-base-q4_0-timeout-20260627-124019.xml`

Summary files:

- `day4-all-runs.csv`
- `day4-model-summary.csv`
- `day4-quality-analysis.csv`

Report charts:

- `day4-size-comparison.svg`
- `day4-rtf-comparison.svg`
