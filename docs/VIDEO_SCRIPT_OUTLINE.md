# English Video Script Outline

Target length: at least 10 minutes.

## 1. Introduction (1 min)

- Introduce the project: deploying ASR models on Android devices.
- Explain why local ASR matters: privacy, offline use, lower network dependency.

## 2. Problem and constraints (1.5 min)

- Model size
- Latency
- Memory
- Battery
- Multilingual accuracy
- Offline inference

## 3. Baseline and related work (1 min)

- Mention the desktop `faster_whisper` baseline from the course repository.
- Explain why desktop Python ASR is different from Android deployment.

## 4. System architecture (1.5 min)

- Show the Android UI.
- Explain audio recording, model selection, JNI bridge, and native ASR backend.

## 5. Android demo (2 min)

- Open the app.
- Select a local model.
- Record speech.
- Transcribe.
- Show that internet permission is not required.

## 6. Benchmark results (1.5 min)

- Show model size, audio duration, inference time, real-time factor, and memory notes.
- Compare English, French, and Chinese if available.

## 7. Limitations and future work (1 min)

- Native backend integration complexity.
- Small model accuracy limitations.
- Future streaming ASR, preprocessing, ONNX comparison, and RAG/LLM transcript correction.

## 8. Team contributions (0.5 min)

- Summarize each member's role and contribution percentage.
