package com.example.asrmobile

import android.content.Context
import android.net.Uri
import java.io.File

class ModelFileManager(private val context: Context) {
    fun copyModelUriToAppStorage(uri: Uri): File {
        val modelsDir = File(context.filesDir, "models").apply { mkdirs() }
        val displayName = queryDisplayName(uri) ?: "selected-model.bin"
        val safeName = displayName.replace(Regex("[^A-Za-z0-9._-]"), "_")
        val outputFile = File(modelsDir, safeName)

        context.contentResolver.openInputStream(uri).use { input ->
            requireNotNull(input) { "Cannot open selected model file." }
            outputFile.outputStream().use { output -> input.copyTo(output) }
        }
        return outputFile
    }

    fun copyBundledModelToAppStorage(): File {
        val modelsDir = File(context.filesDir, "models").apply { mkdirs() }
        val outputFile = File(modelsDir, BUNDLED_MODEL_NAME)
        if (outputFile.exists() && outputFile.length() > 0L) return outputFile

        context.assets.open("models/$BUNDLED_MODEL_NAME").use { input ->
            outputFile.outputStream().use { output -> input.copyTo(output) }
        }
        return outputFile
    }

    fun hasBundledModel(): Boolean = runCatching {
        context.assets.open("models/$BUNDLED_MODEL_NAME").use { true }
    }.getOrDefault(false)

    private fun queryDisplayName(uri: Uri): String? {
        val projection = arrayOf(android.provider.OpenableColumns.DISPLAY_NAME)
        context.contentResolver.query(uri, projection, null, null, null)?.use { cursor ->
            if (cursor.moveToFirst()) {
                val index = cursor.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
                if (index >= 0) return cursor.getString(index)
            }
        }
        return uri.lastPathSegment
    }

    companion object {
        const val BUNDLED_MODEL_NAME = "ggml-tiny.bin"
    }
}
