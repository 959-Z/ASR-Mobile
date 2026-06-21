package com.example.asrmobile

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.media.MediaPlayer
import android.net.Uri
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import java.io.File

class MainActivity : AppCompatActivity() {
    private val modelFileManager by lazy { ModelFileManager(this) }
    private val modelRepository by lazy { ModelRepository(this) }
    private val whisperEngine by lazy { WhisperEngine() }
    private val audioRecorder by lazy { AudioRecorder(this) }
    private val benchmarkRunner by lazy { BenchmarkRunner(this, whisperEngine) }

    private lateinit var statusText: TextView
    private lateinit var transcriptText: TextView
    private lateinit var metricsText: TextView
    private lateinit var audioLanguageInput: EditText
    private lateinit var workflowProgress: ProgressBar
    private lateinit var progressDetailText: TextView
    private lateinit var experimentSummaryText: TextView

    private var selectedModelPath: String? = null
    private var selectedModelName: String = "not selected"
    private var selectedQuantization: String = "unknown"
    private var latestLoadTimeMs: Long? = null
    private var latestRecording: File? = null
    private var busyButtons: List<Button> = emptyList()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 加载前端 XML 布局
        setContentView(R.layout.activity_main)

        // 绑定组件与业务逻辑
        setupViewsAndListeners()

        requestMicrophonePermissionIfNeeded()
        if (!restoreLatestRecording()) {
            updateStatus("Ready. Select a built-in model or pick a model file.")
        }
        handleAutomationIntent(intent)
    }

    private fun setupViewsAndListeners() {
        statusText = findViewById(R.id.tv_status)
        transcriptText = findViewById(R.id.tv_transcript)
        metricsText = findViewById(R.id.tv_metrics)
        audioLanguageInput = findViewById(R.id.et_audio_language)
        workflowProgress = findViewById(R.id.progress_workflow)
        progressDetailText = findViewById(R.id.tv_progress_detail)
        experimentSummaryText = findViewById(R.id.tv_experiment_summary)

        val selectModelButton = findViewById<Button>(R.id.btn_select_model)
        val useBundledButton = findViewById<Button>(R.id.btn_use_bundled)
        val loadModelButton = findViewById<Button>(R.id.btn_load_model)
        val recordButton = findViewById<Button>(R.id.btn_record)
        val transcribeButton = findViewById<Button>(R.id.btn_transcribe)
        val benchmarkButton = findViewById<Button>(R.id.btn_benchmark)
        val playButton = findViewById<Button>(R.id.btn_play)

        busyButtons = listOf(
            selectModelButton,
            useBundledButton,
            loadModelButton,
            recordButton,
            transcribeButton,
            benchmarkButton,
            playButton
        )

        updateExperimentSummary()

        selectModelButton.setOnClickListener {
            selectModelFile()
        }

        useBundledButton.setOnClickListener {
            val builtInModel = modelRepository.getBundledModels().firstOrNull()
            if (builtInModel != null) {
                selectBundledModel(builtInModel)
            } else {
                updateStatus("No built-in models found in assets.")
            }
        }

        loadModelButton.setOnClickListener {
            loadSelectedModel()
        }

        recordButton.setOnClickListener {
            recordShortClip()
        }

        transcribeButton.setOnClickListener {
            transcribeLatestRecording()
        }

        benchmarkButton.setOnClickListener {
            runBenchmark()
        }

        playButton.setOnClickListener {
            playLatestRecording()
        }
    }

    private fun selectBundledModel(model: BundledModel) {
        setBusy(true)
        updateProgress(10, "Preparing bundled model...")
        updateStatus("Preparing ${model.displayName}...")
        selectedModelPath = null
        latestLoadTimeMs = null
        Thread {
            val result = runCatching { modelRepository.deployModel(model).absolutePath }
            runOnUiThread {
                result.onSuccess { path ->
                    selectedModelPath = path
                    selectedModelName = model.displayName
                    selectedQuantization = inferQuantization(model.fileName)
                    updateProgress(25, "Model selected")
                    updateExperimentSummary()
                    updateStatus("Selected built-in model: ${model.displayName}")
                }.onFailure {
                    updateProgress(0, "Model selection failed")
                    updateStatus("Failed to prepare model: ${it.message}")
                }
                setBusy(false)
            }
        }.start()
    }

    private fun selectModelFile() {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "*/*"
        }
        startActivityForResult(intent, REQUEST_MODEL_FILE)
    }

    @Deprecated("Deprecated in AndroidX Activity Result API, but kept simple for this teaching scaffold.")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_MODEL_FILE && resultCode == Activity.RESULT_OK) {
            data?.data?.let { uri ->
                contentResolver.takePersistableUriPermission(
                    uri,
                    Intent.FLAG_GRANT_READ_URI_PERMISSION
                )
                val path = modelFileManager.copyModelUriToAppStorage(uri).absolutePath
                selectedModelPath = path
                selectedModelName = File(path).name
                selectedQuantization = inferQuantization(path)
                latestLoadTimeMs = null
                updateProgress(25, "External model selected")
                updateExperimentSummary()
                updateStatus("Selected external model file: $path")
            }
        }
    }

    private fun selectExternalModelPath(path: String, displayName: String? = null) {
        val file = File(path)
        selectedModelPath = path
        selectedModelName = displayName?.ifBlank { null } ?: file.name
        selectedQuantization = inferQuantization(file.name)
        latestLoadTimeMs = null
        updateProgress(25, "External model selected")
        updateExperimentSummary()
        updateStatus("Selected external model file: $path")
    }

    private fun handleAutomationIntent(intent: Intent?) {
        val path = intent?.getStringExtra(EXTRA_MODEL_PATH) ?: return
        intent.getStringExtra(EXTRA_AUDIO_LANGUAGE)
            ?.takeIf { it.isNotBlank() }
            ?.let { audioLanguageInput.setText(it) }
        selectExternalModelPath(
            path = path,
            displayName = intent.getStringExtra(EXTRA_MODEL_NAME)
        )
        if (intent.getBooleanExtra(EXTRA_AUTO_LOAD, false)) {
            loadSelectedModel(
                afterLoaded = if (intent.getBooleanExtra(EXTRA_AUTO_BENCHMARK, false)) {
                    { runBenchmark() }
                } else {
                    null
                }
            )
        }
    }

    private fun loadSelectedModel(afterLoaded: (() -> Unit)? = null) {
        val path = selectedModelPath
        if (path == null) {
            updateStatus("No model selected. Pick a built-in model or a model file first.")
            return
        }

        setBusy(true)
        updateProgress(35, "Loading selected model...")
        updateStatus("Loading model...")
        Thread {
            val result = runCatching {
                val start = System.nanoTime()
                whisperEngine.loadModel(path)
                (System.nanoTime() - start) / 1_000_000
            }
            runOnUiThread {
                result.onSuccess { loadTimeMs ->
                    latestLoadTimeMs = loadTimeMs
                    updateProgress(50, "Model loaded in ${loadTimeMs} ms")
                    updateExperimentSummary()
                    updateStatus("Model loaded successfully in ${loadTimeMs} ms.")
                    setBusy(false)
                    afterLoaded?.invoke()
                }
                    .onFailure {
                        updateProgress(25, "Model load failed")
                        updateStatus("Model load failed: ${it.message}")
                        setBusy(false)
                    }
            }
        }.start()
    }

    private fun recordShortClip() {
        if (!hasMicrophonePermission()) {
            requestMicrophonePermissionIfNeeded()
            return
        }

        setBusy(true)
        updateProgress(60, "Recording 10 seconds...")
        updateStatus("Recording 10 seconds...")
        Thread {
            val result = runCatching { audioRecorder.recordBlocking(seconds = 10) }
            runOnUiThread {
                result.onSuccess { recording ->
                    latestRecording = recording
                    updateProgress(70, "Recording saved")
                    updateExperimentSummary()
                    updateStatus("Recording saved: ${recording.absolutePath}")
                }.onFailure {
                    updateProgress(50, "Recording failed")
                    updateStatus("Recording failed: ${it.message}")
                }
                setBusy(false)
            }
        }.start()
    }

    private fun restoreLatestRecording(): Boolean {
        val recording = File(filesDir, "recordings/latest.wav")
        if (recording.exists() && recording.length() > 44L) {
            latestRecording = recording
            updateProgress(70, "Restored latest recording")
            updateExperimentSummary()
            updateStatus("Restored recording: ${recording.absolutePath}")
            return true
        }
        return false
    }

    private fun transcribeLatestRecording() {
        val recording = latestRecording
        if (recording == null) {
            updateStatus("No recording yet.")
            return
        }

        setBusy(true)
        updateProgress(80, "Transcribing latest recording...")
        updateStatus("Transcribing ${recording.name}...")
        Thread {
            val result = runCatching { whisperEngine.transcribe(recording.absolutePath) }
            runOnUiThread {
                result.onSuccess {
                    transcriptText.text = it
                    updateProgress(100, "Transcription finished")
                }.onFailure {
                    transcriptText.text = "Transcription failed: ${it.message}"
                    updateProgress(70, "Transcription failed")
                }
                updateStatus("Transcription finished.")
                setBusy(false)
            }
        }.start()
    }

    private fun playLatestRecording() {
        val recording = latestRecording
        if (recording == null || !recording.exists()) {
            updateStatus("No recording yet.")
            return
        }

        updateStatus("Playing ${recording.name}...")
        MediaPlayer().apply {
            try {
                setDataSource(recording.absolutePath)
                prepare()
                start()
                setOnCompletionListener {
                    release()
                    runOnUiThread { updateStatus("Playback finished.") }
                }
                // ✅ 修复点 1：正确的原生 Android 监听器名
                setOnErrorListener { _, what, extra ->
                    release()
                    runOnUiThread { updateStatus("Playback error: $what / $extra") }
                    true
                }
            } catch (e: Exception) {
                release()
                updateStatus("Playback failed: ${e.message}")
            }
        }
    }

    private fun runBenchmark() {
        val recording = latestRecording
        if (recording == null) {
            updateStatus("Record a clip before benchmarking.")
            return
        }

        setBusy(true)
        updateProgress(75, "Benchmark starting...")
        Thread {
            val report = benchmarkRunner.benchmark(
                audioFile = recording,
                modelPath = selectedModelPath,
                modelName = selectedModelName,
                quantization = selectedQuantization,
                audioLanguage = audioLanguage(),
                loadTimeMs = latestLoadTimeMs,
                repetitions = 3,
                onProgress = { runIndex, totalRuns ->
                    runOnUiThread {
                        val progress = 75 + (runIndex - 1) * 20 / totalRuns
                        updateProgress(progress, "Benchmark run $runIndex / $totalRuns")
                    }
                }
            )
            val exportFile = benchmarkRunner.exportCsv(report)
            runOnUiThread {
                updateProgress(100, "Benchmark finished")
                updateExperimentSummary()
                metricsText.text = report.toDisplayText(exportFile)
                updateStatus("Benchmark finished. CSV saved: ${exportFile.absolutePath}")
                setBusy(false)
            }
        }.start()
    }

    private fun requestMicrophonePermissionIfNeeded() {
        if (!hasMicrophonePermission()) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.RECORD_AUDIO),
                REQUEST_RECORD_AUDIO
            )
        }
    }

    private fun hasMicrophonePermission(): Boolean =
        ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED

    private fun updateStatus(message: String) {
        statusText.text = message
    }

    private fun updateProgress(progress: Int, detail: String) {
        workflowProgress.progress = progress.coerceIn(0, 100)
        progressDetailText.text = detail
    }

    private fun updateExperimentSummary() {
        val modelSize = selectedModelPath
            ?.let { File(it).takeIf(File::exists)?.length()?.toDouble()?.div(1024.0 * 1024.0) }
            ?.let { "% .2f MB".format(it).trim() }
            ?: "unknown"
        val recording = latestRecording
        val recordingSummary = if (recording != null && recording.exists()) {
            "${recording.name}, ${"% .2f KB".format(recording.length() / 1024.0).trim()}"
        } else {
            "none"
        }
        experimentSummaryText.text = buildString {
            appendLine("Model: $selectedModelName ($selectedQuantization, $modelSize)")
            appendLine("Recording: $recordingSummary")
            appendLine("Load time: ${latestLoadTimeMs?.toString() ?: "unknown"} ms")
            append("Language: ${audioLanguage()}")
        }
    }

    private fun setBusy(isBusy: Boolean) {
        busyButtons.forEach { it.isEnabled = !isBusy }
    }

    private fun audioLanguage(): String =
        audioLanguageInput.text?.toString()?.trim()?.ifBlank { "unknown" } ?: "unknown"

    private fun inferQuantization(value: String): String {
        val normalized = value.lowercase()
        return when {
            "q8" in normalized -> "Q8"
            "q5" in normalized -> "Q5"
            "q4" in normalized -> "Q4"
            "fp16" in normalized || "f16" in normalized -> "FP16"
            "fp32" in normalized || "f32" in normalized -> "FP32"
            else -> "unknown"
        }
    }

    companion object {
        private const val REQUEST_RECORD_AUDIO = 1001
        private const val REQUEST_MODEL_FILE = 1002
        private const val EXTRA_MODEL_PATH = "model_path"
        private const val EXTRA_MODEL_NAME = "model_name"
        private const val EXTRA_AUTO_LOAD = "auto_load"
        private const val EXTRA_AUTO_BENCHMARK = "auto_benchmark"
        private const val EXTRA_AUDIO_LANGUAGE = "audio_language"
    }
}
