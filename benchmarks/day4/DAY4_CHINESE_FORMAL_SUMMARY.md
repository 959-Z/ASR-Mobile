# Day 4 Chinese Formal Benchmark Summary

## Test Setup

| Field | Value |
|---|---|
| Date | 2026-06-21 |
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
| `ggml-tiny-q5_1.bin` | Q5 | 30.66 | 253 | 108814.67 | 10.882 | 13.23x slower | success |
| `ggml-base-q8_0.bin` | Q8 | 77.98 | 203 | 111234.33 | 11.123 | 13.52x slower | success |
| `ggml-base-q5_1.bin` | Q5 | 56.94 | unknown | timeout | timeout | timeout | timeout |

## Size Reduction

Using `ggml-tiny.bin` as the tiny baseline:

| Model | Size MB | Size vs tiny baseline | Reduction vs tiny baseline |
|---|---:|---:|---:|
| `ggml-tiny.bin` | 74.09 | 100.00% | 0.00% |
| `ggml-tiny-q8_0.bin` | 41.52 | 56.04% | 43.96% |
| `ggml-tiny-q5_1.bin` | 30.66 | 41.38% | 58.62% |

Using `ggml-base.bin` as the base baseline from A's model matrix:

| Model | Size MB | Size vs base baseline | Reduction vs base baseline |
|---|---:|---:|---:|
| `ggml-base.bin` | 141.10 | 100.00% | 0.00% |
| `ggml-base-q8_0.bin` | 77.98 | 55.27% | 44.73% |
| `ggml-base-q5_1.bin` | 56.94 | 40.35% | 59.65% |

## Recognition Quality Notes

The tiny baseline remained the most practical result in this formal Chinese run. It achieved RTF < 1, meaning it was faster than real time on the Huawei phone.

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
6. Base Q5 loaded successfully in Day 2 validation, but timed out during formal Day 4 benchmark.

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

Summary files:

- `day4-all-runs.csv`
- `day4-model-summary.csv`
