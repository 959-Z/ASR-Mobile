# Day 2 Android Model Loading Validation

## Purpose

This document records B-side Android validation for the model files provided by A. The goal of this step is not to benchmark recognition speed yet, but to confirm that each quantized GGML model can be placed on the Huawei phone and loaded by the Android whisper.cpp backend.

## Device

| Field | Value |
|---|---|
| Device | HUAWEI HBN-AL10 |
| Android version | 12 |
| ABI | arm64-v8a |
| App package | `com.example.asrmobile` |
| Validation date | 2026-06-20 |

## Model Transfer Result

The model files from A's `ASR-Mobile.zip` were extracted into the current repository `models/` directory without overwriting existing Android code.

For Android validation, models were copied into the app private model directory:

```text
/data/user/0/com.example.asrmobile/files/models/
```

An external app-specific storage path was also tested:

```text
/sdcard/Android/data/com.example.asrmobile/files/models/
```

The external path caused model loading failure for `ggml-tiny-q8_0.bin`, while the private app path loaded successfully. Therefore, the private app path is used for the formal Day 4 benchmark.

## Loading Validation Matrix

| Order | Model file | Model scale | Quantization | Size MiB | Android load result | Load time ms | Notes |
|---:|---|---|---|---:|---|---:|---|
| 1 | `ggml-tiny-q8_0.bin` | tiny | Q8 | 41.52 | success | 140 | Loaded from app private model path |
| 2 | `ggml-tiny-q5_1.bin` | tiny | Q5 | 30.66 | success | 125 | Loaded from app private model path |
| 3 | `ggml-tiny-q4_0.bin` | tiny | Q4 | 24.15 | success | 127 | Loaded from app private model path |
| 4 | `ggml-base-q8_0.bin` | base | Q8 | 77.98 | success | 165 | Loaded from app private model path |
| 5 | `ggml-base-q5_1.bin` | base | Q5 | 56.94 | success | 152 | Loaded from app private model path |
| 6 | `ggml-base-q4_0.bin` | base | Q4 | 44.32 | success | 137 | Loaded from app private model path |
| 7 | `ggml-base.bin` | base | baseline | 141.10 | success | 212 | Loaded from app private model path |

Baseline bundled model already validated earlier:

| Model file | Model scale | Quantization | Size MiB | Android load result | Recent load time ms |
|---|---|---|---:|---|---:|
| `ggml-tiny.bin` | tiny | baseline | 74.09 | success | 204 |

## B-Side Conclusion

A's Day 2 model package is usable for Android-side experiments. All required tiny and base quantized models can be loaded by the Android app when stored under the app private model directory.

This means Day 4 can proceed with formal benchmark tests using:

- tiny baseline: `ggml-tiny.bin`
- tiny quantized: `ggml-tiny-q8_0.bin`, `ggml-tiny-q5_1.bin`, `ggml-tiny-q4_0.bin`
- base baseline: `ggml-base.bin`
- base quantized: `ggml-base-q8_0.bin`, `ggml-base-q5_1.bin`, `ggml-base-q4_0.bin`

## Practical Note For Day 4

For reliable Android benchmark runs, use the app private path:

```text
/data/user/0/com.example.asrmobile/files/models/<model-file>
```

Avoid using:

```text
/sdcard/Android/data/com.example.asrmobile/files/models/<model-file>
```

because at least one model failed to load from that external path even though the file was present.
