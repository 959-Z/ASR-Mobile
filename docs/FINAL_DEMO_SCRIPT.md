# Final Demo Script

## Opening

This project is ASR-Mobile, an Android offline speech recognition deployment project. It runs local recording, local model loading, local whisper.cpp inference, and benchmark export on a phone.

## Demo Steps

1. Open the Android app.
2. Show the experiment summary area.
3. Select or load the tiny model.
4. Record a 10-second audio clip.
5. Run transcription.
6. Run performance benchmark.
7. Show exported benchmark CSV.
8. Show Day 4 result table.

## Result Explanation

The most practical model in our experiment is `ggml-tiny.bin`.

It achieved:

- model size: 74.09 MB
- average inference time: 8226.67 ms
- average RTF: 0.822

Since RTF is below 1, it runs faster than real time on the tested Huawei Android phone.

## Quantization Explanation

Quantized models were smaller:

- tiny Q8 reduced size by about 43.96%
- tiny Q5 reduced size by about 58.62%

However, they were slower on this Android backend. This shows that compression does not automatically mean faster mobile inference.

## Closing

The final conclusion is that mobile ASR deployment must be evaluated with real device data. For this project, `ggml-tiny.bin` gives the best balance between size, speed, and recognition usability.
