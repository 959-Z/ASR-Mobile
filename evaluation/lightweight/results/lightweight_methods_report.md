# Lightweight Methods Experiment Report

## Setup

- Teacher: `openai/whisper-base`
- Student: `openai/whisper-tiny`
- Samples: 9 local benchmark audio files
- Device: `NVIDIA GeForce RTX 4060 Laptop GPU`
- Cache root: `D:\ml课程项目\.cache`

## Summary

| Method | Samples | Accuracy | Latency ms | RTF | Dense size MB | Linear sparsity |
|---|---:|---:|---:|---:|---:|---:|
| distilled-tiny | 9 | 92.9% | 41 | 0.02 | 72.0 | 0.0% |
| pruned-20-recovery | 9 | 90.1% | 43 | 0.02 | 72.0 | 20.0% |
| pruned-10 | 9 | 89.2% | 86 | 0.04 | 72.0 | 10.0% |
| pruned-20 | 9 | 86.9% | 111 | 0.06 | 72.0 | 20.0% |
| tiny-baseline | 9 | 83.2% | 94 | 0.05 | 72.0 | 0.0% |
| pruned-30 | 9 | 80.7% | 122 | 0.06 | 72.0 | 30.0% |

## Interpretation Notes

- Distillation is implemented as sequence-level pseudo-label distillation from the teacher model.
- Magnitude pruning creates zero weights, but dense PyTorch/whisper runtimes may not translate that sparsity into speedup.
- Recovery fine-tuning tests whether a pruned student can regain quality after compression.
- These results are PC/GPU-side research evidence; Android deployment still depends on GGML/GGUF conversion and runtime support.