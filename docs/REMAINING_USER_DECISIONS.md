# Remaining User Decisions

Most implementation, benchmarking, and report-preparation work for the quantization/compression direction is complete. The remaining items need user or teammate confirmation.

## Decisions Needed

| Decision | Why it matters | Recommended choice |
|---|---|---|
| Whether to run English benchmark | Needed only if final submission requires multilingual evidence | Optional; Chinese formal run is already sufficient for model trade-off analysis |
| Whether to run French benchmark | Adds language coverage but costs time | Skip unless course rubric explicitly asks |
| Whether to push large model files | Model files greatly increase repository size | Do not push unless the team accepts large repository size |
| Whether to include Q4 formal benchmark | Q4 may be very slow or unstable | Mention Q4 as prepared/validated, but not part of core formal result |
| Whether A agrees with final wording | Report should align model-side and Android-side conclusions | Ask A to review `PROJECT_REPORT.md` and `docs/FINAL_DELIVERY_REVIEW.md` |

## Current Recommended Final Position

Use the current Chinese formal benchmark as the main result.

Final model recommendation:

```text
ggml-tiny.bin
```

Main conclusion:

```text
Quantization reduced model size, but did not improve speed on this Android whisper.cpp backend. Real mobile deployment requires device-side measurement, not only theoretical compression analysis.
```
