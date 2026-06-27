# Lightweight ASR Compression Research

## Research Question

The project studies how to make Whisper practical for Android offline ASR. The core question is not only which model is most accurate, but which compression path gives the best deployment trade-off among model size, loading time, inference latency, RTF, multilingual quality, and Android runtime compatibility.

## Related Work

Whisper shows strong multilingual ASR ability through large-scale weak supervision, but the model family still has non-trivial deployment cost on mobile devices. Distil-Whisper demonstrates that sequence-level distillation and pseudo labelling can transfer part of Whisper's performance into smaller/faster students. Quantization-oriented work such as DQ-Whisper/Whisper-KDQ shows that lower-bit inference and distillation can be combined. CTranslate2 and whisper.cpp represent engineering-oriented inference runtimes where quantization is a practical path for CPU/mobile deployment. Model compression surveys also identify quantization, pruning, low-rank factorization, and knowledge distillation as the main compression families.

References used:

- Whisper: https://arxiv.org/abs/2212.04356
- Distil-Whisper: https://arxiv.org/abs/2311.00430
- DQ-Whisper / Whisper-KDQ: https://arxiv.org/html/2305.10788v2
- CTranslate2 quantization: https://opennmt.net/CTranslate2/quantization.html
- CTranslate2 runtime optimizations: https://github.com/OpenNMT/CTranslate2
- Model compression survey: https://pmc.ncbi.nlm.nih.gov/articles/PMC11965593/
- Whisper pruning/adaptation reference: https://aclanthology.org/2023.mrl-1.7.pdf

## Methods Compared

| Method | Project implementation | Purpose | Android status |
|---|---|---|---|
| Architecture scaling | `tiny` vs `base` | Compare smaller architecture against larger multilingual model | Directly applicable |
| GGML quantization | baseline/Q8/Q5/Q4 for `tiny` and `base` | Reduce model file size and CPU inference cost | Main Android path |
| Pseudo-label distillation | `openai/whisper-base` teacher -> `openai/whisper-tiny` student | Test whether teacher supervision can improve a small model | Research-side result |
| Magnitude pruning | 10%, 20%, 30% Linear-layer pruning | Test parameter sparsity and quality loss | Not directly useful without sparse runtime |
| Pruning recovery training | 20% pruning + short recovery fine-tuning | Test whether training can recover pruned model quality | Research-side result |

## Own Experiments

### Quantization Matrix

The GGML quantization experiment tested 8 models on 9 short audio files across English, Chinese, and French. The best low-resource candidate was `ggml-tiny-q4_0.bin`, with 24.15 MB size, 525 ms average inference time, RTF 0.27, and 90.1% average accuracy. The best quality candidate was `ggml-base-q4_0.bin`, with 44.32 MB size, 1087 ms average inference time, RTF 0.56, and 98.4% average accuracy.

### GPU Lightweight Compression Experiment

The second experiment used the RTX 4060 Laptop GPU and the existing 9 local benchmark audio files. It implemented three training/compression methods: pseudo-label distillation, magnitude pruning, and pruning recovery fine-tuning.

| Method | Accuracy | Latency ms | RTF | Dense size MB | Linear sparsity |
|---|---:|---:|---:|---:|---:|
| distilled-tiny | 92.9% | 41 | 0.02 | 72.0 | 0.0% |
| pruned-20-recovery | 90.1% | 43 | 0.02 | 72.0 | 20.0% |
| pruned-10 | 89.2% | 86 | 0.04 | 72.0 | 10.0% |
| pruned-20 | 86.9% | 111 | 0.06 | 72.0 | 20.0% |
| tiny-baseline | 83.2% | 94 | 0.05 | 72.0 | 0.0% |
| pruned-30 | 80.7% | 122 | 0.06 | 72.0 | 30.0% |

The distillation result improved the small model on this short benchmark, but the experiment is still small-scale and should not be treated as a full Distil-Whisper reproduction. Pruning showed a clearer trade-off: higher sparsity reduces the number of active Linear weights, but dense PyTorch/whisper runtimes do not automatically convert unstructured sparsity into lower file size or faster inference. Recovery fine-tuning helped recover quality after 20% pruning.

## Interpretation

The main engineering conclusion is that compression methods differ in deployment readiness. Quantization is the most Android-ready method because whisper.cpp directly supports GGML quantized models. Distillation can improve a small student model, but it requires training and then a reliable conversion path before Android deployment. Pruning is useful for research analysis, but ordinary unstructured pruning is not enough for mobile speedup unless the runtime supports sparse kernels or structured pruning.

Therefore, the recommended Android path remains GGML quantization, while distillation and pruning are treated as research extensions. A practical next step is to combine the best student checkpoint with GGUF/GGML conversion and then apply Q8/Q4 quantization, but that requires additional compatibility validation.

## Limitations

- The GPU compression experiment uses only 9 local benchmark files, so it is a controlled small-scale study.
- Distillation uses sequence-level pseudo labels rather than full logit-level knowledge distillation.
- Pruning is unstructured magnitude pruning; it does not reduce dense checkpoint size without sparse storage.
- Android performance must still be measured on device because GPU-side PyTorch results do not represent mobile CPU/JNI behavior.

## Conclusion

The project now covers multiple lightweight ASR methods instead of only comparing quantized files. Quantization is the strongest deployment method, distillation is promising for improving small-model quality, and pruning is informative but needs sparse or structured runtime support before it can become a practical Android optimization.
