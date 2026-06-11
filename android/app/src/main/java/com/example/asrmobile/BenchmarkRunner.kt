package com.example.asrmobile

import android.content.Context
import android.os.Build
import android.os.Debug
import java.io.File

class BenchmarkRunner(
    private val context: Context,
    private val whisperEngine: WhisperEngine
) {
    fun benchmark(audioFile: File, modelPath: String?): BenchmarkResult {
        val startJavaHeap = usedJavaHeapBytes()
        val startNativeHeap = Debug.getNativeHeapAllocatedSize()
        val start = System.nanoTime()

        val transcript = runCatching { whisperEngine.transcribe(audioFile.absolutePath) }
            .getOrElse { "Benchmark transcription failed: ${it.message}" }

        val end = System.nanoTime()
        val endJavaHeap = usedJavaHeapBytes()
        val endNativeHeap = Debug.getNativeHeapAllocatedSize()
        val inferenceMs = (end - start) / 1_000_000
        val audioSeconds = estimateWavDurationSeconds(audioFile)
        val rtf = if (audioSeconds > 0.0) inferenceMs / 1000.0 / audioSeconds else Double.NaN

        return BenchmarkResult(
            device = "${Build.MANUFACTURER} ${Build.MODEL}",
            androidVersion = Build.VERSION.RELEASE ?: "unknown",
            abi = Build.SUPPORTED_ABIS.firstOrNull() ?: "unknown",
            modelPath = modelPath ?: "not selected",
            modelSizeMb = modelPath?.let { File(it).takeIf(File::exists)?.length()?.toDouble()?.div(1024.0 * 1024.0) },
            audioFile = audioFile.name,
            audioSeconds = audioSeconds,
            inferenceMs = inferenceMs,
            realTimeFactor = rtf,
            javaHeapDeltaMb = (endJavaHeap - startJavaHeap).toDouble() / (1024.0 * 1024.0),
            nativeHeapDeltaMb = (endNativeHeap - startNativeHeap).toDouble() / (1024.0 * 1024.0),
            transcript = transcript
        )
    }

    private fun usedJavaHeapBytes(): Long = Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory()

    private fun estimateWavDurationSeconds(file: File): Double {
        if (!file.exists() || file.length() <= 44L) return 0.0
        val pcmBytes = file.length() - 44L
        val bytesPerSecond = 16_000 * 2
        return pcmBytes.toDouble() / bytesPerSecond.toDouble()
    }
}

data class BenchmarkResult(
    val device: String,
    val androidVersion: String,
    val abi: String,
    val modelPath: String,
    val modelSizeMb: Double?,
    val audioFile: String,
    val audioSeconds: Double,
    val inferenceMs: Long,
    val realTimeFactor: Double,
    val javaHeapDeltaMb: Double,
    val nativeHeapDeltaMb: Double,
    val transcript: String
) {
    fun toDisplayText(): String = buildString {
        appendLine("Device: $device")
        appendLine("Android: $androidVersion")
        appendLine("ABI: $abi")
        appendLine("Model: $modelPath")
        appendLine("Model size: ${modelSizeMb?.format(2) ?: "unknown"} MB")
        appendLine("Audio: $audioFile (${audioSeconds.format(2)} s)")
        appendLine("Inference time: $inferenceMs ms")
        appendLine("RTF: ${realTimeFactor.format(3)}")
        appendLine("Java heap delta: ${javaHeapDeltaMb.format(2)} MB")
        appendLine("Native heap delta: ${nativeHeapDeltaMb.format(2)} MB")
        appendLine("Transcript preview:")
        appendLine(transcript.take(500))
    }

    private fun Double.format(digits: Int): String = "% .${digits}f".format(this).trim()
}
