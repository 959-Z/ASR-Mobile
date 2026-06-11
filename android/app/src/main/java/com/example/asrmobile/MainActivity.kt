package com.example.asrmobile

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import java.io.File

class MainActivity : AppCompatActivity() {
    private val modelFileManager by lazy { ModelFileManager(this) }
    private val whisperEngine by lazy { WhisperEngine() }
    private val audioRecorder by lazy { AudioRecorder(this) }
    private val benchmarkRunner by lazy { BenchmarkRunner(this, whisperEngine) }

    private lateinit var statusText: TextView
    private lateinit var transcriptText: TextView
    private lateinit var metricsText: TextView

    private var selectedModelUri: Uri? = null
    private var selectedModelPath: String? = null
    private var latestRecording: File? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        buildUi()
        requestMicrophonePermissionIfNeeded()
        updateStatus("Ready. Select a local model file before transcription.")
    }

    private fun buildUi() {
        statusText = TextView(this).withPadding()
        transcriptText = TextView(this).withPadding()
        metricsText = TextView(this).withPadding()

        val selectModelButton = Button(this).apply {
            text = "Select model file"
            setOnClickListener { selectModelFile() }
        }
        val useBundledModelButton = Button(this).apply {
            text = "Use bundled tiny model"
            setOnClickListener { useBundledModel() }
        }
        val loadModelButton = Button(this).apply {
            text = "Load model"
            setOnClickListener { loadSelectedModel() }
        }
        val recordButton = Button(this).apply {
            text = "Record 10 seconds"
            setOnClickListener { recordShortClip() }
        }
        val transcribeButton = Button(this).apply {
            text = "Transcribe latest recording"
            setOnClickListener { transcribeLatestRecording() }
        }
        val benchmarkButton = Button(this).apply {
            text = "Run benchmark"
            setOnClickListener { runBenchmark() }
        }

        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(24, 24, 24, 24)
            addView(TextView(context).apply {
                text = "ASR Mobile"
                textSize = 24f
            })
            addView(statusText)
            addView(selectModelButton)
            addView(useBundledModelButton)
            addView(loadModelButton)
            addView(recordButton)
            addView(transcribeButton)
            addView(benchmarkButton)
            addView(TextView(context).apply { text = "Transcript"; textSize = 18f })
            addView(transcriptText)
            addView(TextView(context).apply { text = "Metrics"; textSize = 18f })
            addView(metricsText)
        }

        setContentView(ScrollView(this).apply { addView(content) })
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
            selectedModelUri = data?.data
            selectedModelUri?.let { uri ->
                contentResolver.takePersistableUriPermission(
                    uri,
                    Intent.FLAG_GRANT_READ_URI_PERMISSION
                )
                selectedModelPath = modelFileManager.copyModelUriToAppStorage(uri).absolutePath
                updateStatus("Selected model: $selectedModelPath")
            }
        }
    }

    private fun useBundledModel() {
        if (!modelFileManager.hasBundledModel()) {
            updateStatus("Bundled model not found in APK assets. Add ggml-tiny.bin to app/src/main/assets/models/ and rebuild.")
            return
        }

        updateStatus("Copying bundled model to app storage...")
        Thread {
            val result = runCatching { modelFileManager.copyBundledModelToAppStorage().absolutePath }
            runOnUiThread {
                result.onSuccess { path ->
                    selectedModelPath = path
                    updateStatus("Bundled model ready: $path")
                }.onFailure {
                    updateStatus("Bundled model copy failed: ${it.message}")
                }
            }
        }.start()
    }

    private fun loadSelectedModel() {
        val path = selectedModelPath
        if (path == null) {
            updateStatus("No model selected. This app does not download models.")
            return
        }

        runCatching { whisperEngine.loadModel(path) }
            .onSuccess { updateStatus("Model load requested: $path") }
            .onFailure { updateStatus("Model load failed: ${it.message}") }
    }

    private fun recordShortClip() {
        if (!hasMicrophonePermission()) {
            requestMicrophonePermissionIfNeeded()
            return
        }

        updateStatus("Recording 10 seconds...")
        Thread {
            val recording = audioRecorder.recordBlocking(seconds = 10)
            latestRecording = recording
            runOnUiThread { updateStatus("Recording saved: ${recording.absolutePath}") }
        }.start()
    }

    private fun transcribeLatestRecording() {
        val recording = latestRecording
        if (recording == null) {
            updateStatus("No recording yet.")
            return
        }

        updateStatus("Transcribing ${recording.name}...")
        Thread {
            val result = runCatching { whisperEngine.transcribe(recording.absolutePath) }
            runOnUiThread {
                result.onSuccess { transcriptText.text = it }
                    .onFailure { transcriptText.text = "Transcription failed: ${it.message}" }
                updateStatus("Transcription finished.")
            }
        }.start()
    }

    private fun runBenchmark() {
        val recording = latestRecording
        if (recording == null) {
            updateStatus("Record a clip before benchmarking.")
            return
        }

        Thread {
            val result = benchmarkRunner.benchmark(recording, selectedModelPath)
            runOnUiThread { metricsText.text = result.toDisplayText() }
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

    private fun TextView.withPadding(): TextView = apply { setPadding(0, 12, 0, 12) }

    companion object {
        private const val REQUEST_RECORD_AUDIO = 1001
        private const val REQUEST_MODEL_FILE = 1002
    }
}
