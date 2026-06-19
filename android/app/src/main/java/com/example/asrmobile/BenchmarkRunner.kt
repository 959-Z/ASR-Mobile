package com.example.asrmobile

import android.content.Context
import android.os.Build
import android.os.Debug
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class BenchmarkRunner(
    private val context: Context,
    private val whisperEngine: WhisperEngine
) {
    fun benchmark(
        audioFile: File,
        modelPath: String?,
        modelName: String,
        quantization: String,
        loadTimeMs: Long?,
        repetitions: Int
    ): BenchmarkReport {
        val runs = (1..maxOf(1, repetitions)).map { runIndex ->
            benchmarkOnce(
                audioFile = audioFile,
                modelPath = modelPath,
                modelName = modelName,
                quantization = quantization,
                loadTimeMs = loadTimeMs,
                runIndex = runIndex
            )
        }
        return BenchmarkReport(runs)
    }

    private fun benchmarkOnce(
        audioFile: File,
        modelPath: String?,
        modelName: String,
        quantization: String,
        loadTimeMs: Long?,
        runIndex: Int
    ): BenchmarkResult {
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
            timestamp = timestamp(),
            runIndex = runIndex,
            device = "${Build.MANUFACTURER} ${Build.MODEL}",
            androidVersion = Build.VERSION.RELEASE ?: "unknown",
            abi = Build.SUPPORTED_ABIS.firstOrNull() ?: "unknown",
            modelName = modelName,
            quantization = quantization,
            modelPath = modelPath ?: "not selected",
            modelSizeMb = modelPath?.let { File(it).takeIf(File::exists)?.length()?.toDouble()?.div(1024.0 * 1024.0) },
            audioFile = audioFile.name,
            audioSeconds = audioSeconds,
            loadTimeMs = loadTimeMs,
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

    private fun timestamp(): String =
        SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US).format(Date())

    fun exportCsv(report: BenchmarkReport): File {
        val dir = File(context.filesDir, "benchmarks").apply { mkdirs() }
        val file = File(dir, "benchmark-${System.currentTimeMillis()}.csv")
        file.writeText(report.toCsv())
        return file
    }
}

data class BenchmarkResult(
    val timestamp: String,
    val runIndex: Int,
    val device: String,
    val androidVersion: String,
    val abi: String,
    val modelName: String,
    val quantization: String,
    val modelPath: String,
    val modelSizeMb: Double?,
    val audioFile: String,
    val audioSeconds: Double,
    val loadTimeMs: Long?,
    val inferenceMs: Long,
    val realTimeFactor: Double,
    val javaHeapDeltaMb: Double,
    val nativeHeapDeltaMb: Double,
    val transcript: String
) {
    fun toCsvRow(): String = listOf(
        timestamp,
        runIndex.toString(),
        device,
        androidVersion,
        abi,
        modelName,
        quantization,
        modelPath,
        modelSizeMb?.format(2) ?: "",
        audioFile,
        audioSeconds.format(2),
        loadTimeMs?.toString() ?: "",
        inferenceMs.toString(),
        realTimeFactor.format(3),
        javaHeapDeltaMb.format(2),
        nativeHeapDeltaMb.format(2),
        transcript,
        "",
        ""
    ).joinToString(",") { it.csvEscape() }

    private fun String.csvEscape(): String {
        val escaped = replace("\"", "\"\"").replace("\n", " ").replace("\r", " ")
        return "\"$escaped\""
    }

    fun toDisplayText(): String = buildString {
        appendLine("Run: $runIndex")
        appendLine("Device: $device")
        appendLine("Android: $androidVersion")
        appendLine("ABI: $abi")
        appendLine("Model name: $modelName")
        appendLine("Quantization: $quantization")
        appendLine("Model: $modelPath")
        appendLine("Model size: ${modelSizeMb?.format(2) ?: "unknown"} MB")
        appendLine("Audio: $audioFile (${audioSeconds.format(2)} s)")
        appendLine("Load time: ${loadTimeMs?.toString() ?: "unknown"} ms")
        appendLine("Inference time: $inferenceMs ms")
        appendLine("RTF: ${realTimeFactor.format(3)}")
        appendLine("Java heap delta: ${javaHeapDeltaMb.format(2)} MB")
        appendLine("Native heap delta: ${nativeHeapDeltaMb.format(2)} MB")
        appendLine("Transcript preview:")
        appendLine(transcript.take(500))
    }

    private fun Double.format(digits: Int): String = "% .${digits}f".format(this).trim()
}

data class BenchmarkReport(
    val runs: List<BenchmarkResult>
) {
    private val averageInferenceMs: Double =
        runs.map { it.inferenceMs }.averageOrNaN()
    private val averageRtf: Double =
        runs.map { it.realTimeFactor }.averageOrNaN()
    private val averageJavaHeapDeltaMb: Double =
        runs.map { it.javaHeapDeltaMb }.averageOrNaN()
    private val averageNativeHeapDeltaMb: Double =
        runs.map { it.nativeHeapDeltaMb }.averageOrNaN()

    fun toDisplayText(exportFile: File): String = buildString {
        val first = runs.firstOrNull()
        if (first == null) {
            appendLine("No benchmark runs.")
            return@buildString
        }
        appendLine("Benchmark summary")
        appendLine("Device: ${first.device}")
        appendLine("Android: ${first.androidVersion}")
        appendLine("ABI: ${first.abi}")
        appendLine("Model name: ${first.modelName}")
        appendLine("Quantization: ${first.quantization}")
        appendLine("Model path: ${first.modelPath}")
        appendLine("Model size: ${first.modelSizeMb?.format(2) ?: "unknown"} MB")
        appendLine("Audio: ${first.audioFile} (${first.audioSeconds.format(2)} s)")
        appendLine("Load time: ${first.loadTimeMs?.toString() ?: "unknown"} ms")
        appendLine("Repetitions: ${runs.size}")
        appendLine("Average inference time: ${averageInferenceMs.format(2)} ms")
        appendLine("Average RTF: ${averageRtf.format(3)}")
        appendLine("Average Java heap delta: ${averageJavaHeapDeltaMb.format(2)} MB")
        appendLine("Average native heap delta: ${averageNativeHeapDeltaMb.format(2)} MB")
        appendLine("CSV: ${exportFile.absolutePath}")
        appendLine()
        appendLine("Runs")
        runs.forEach {
            appendLine("#${it.runIndex}: ${it.inferenceMs} ms, RTF ${it.realTimeFactor.format(3)}")
        }
        appendLine()
        appendLine("Transcript preview:")
        appendLine(first.transcript.take(500))
    }

    fun toCsv(): String = buildString {
        appendLine(
            listOf(
                "timestamp",
                "run_index",
                "device",
                "android_version",
                "abi",
                "model_name",
                "quantization",
                "model_path",
                "model_size_mb",
                "audio_file",
                "audio_duration_s",
                "load_time_ms",
                "inference_time_ms",
                "rtf",
                "java_heap_delta_mb",
                "native_heap_delta_mb",
                "transcript",
                "quality_score",
                "notes"
            ).joinToString(",")
        )
        runs.forEach { appendLine(it.toCsvRow()) }
    }

    private fun List<Double>.averageOrNaN(): Double =
        if (isEmpty()) Double.NaN else average()

    private fun Double.format(digits: Int): String = "% .${digits}f".format(this).trim()
}
