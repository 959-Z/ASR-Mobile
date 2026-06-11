package com.example.asrmobile

class WhisperEngine {
    private var nativeHandle: Long = 0L

    fun loadModel(modelPath: String) {
        nativeHandle = initModel(modelPath)
        if (nativeHandle == 0L) {
            error("Native whisper.cpp backend is not configured yet, or the model could not be loaded.")
        }
    }

    fun transcribe(wavPath: String): String {
        if (nativeHandle == 0L) {
            error("Model is not loaded. Select a local model file first. This app does not download models.")
        }
        return transcribeFromFile(nativeHandle, wavPath)
    }

    fun release() {
        if (nativeHandle != 0L) {
            releaseModel(nativeHandle)
            nativeHandle = 0L
        }
    }

    protected fun finalize() {
        release()
    }

    private external fun initModel(modelPath: String): Long
    private external fun transcribeFromFile(handle: Long, wavPath: String): String
    private external fun releaseModel(handle: Long)

    companion object {
        init {
            System.loadLibrary("asr_mobile")
        }
    }
}
