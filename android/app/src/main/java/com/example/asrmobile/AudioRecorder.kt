package com.example.asrmobile

import android.content.Context
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import java.io.File
import java.io.FileOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder

class AudioRecorder(private val context: Context) {
    private val sampleRate = 16_000
    private val channelConfig = AudioFormat.CHANNEL_IN_MONO
    private val audioFormat = AudioFormat.ENCODING_PCM_16BIT

    fun recordBlocking(seconds: Int): File {
        val minBufferSize = AudioRecord.getMinBufferSize(sampleRate, channelConfig, audioFormat)
        val bufferSize = maxOf(minBufferSize, sampleRate * 2)
        val pcmData = ByteArray(sampleRate * seconds * 2)

        val recorder = AudioRecord(
            MediaRecorder.AudioSource.MIC,
            sampleRate,
            channelConfig,
            audioFormat,
            bufferSize
        )

        var offset = 0
        recorder.startRecording()
        while (offset < pcmData.size) {
            val read = recorder.read(pcmData, offset, pcmData.size - offset)
            if (read > 0) offset += read
        }
        recorder.stop()
        recorder.release()

        val dir = File(context.filesDir, "recordings").apply { mkdirs() }
        val wavFile = File(dir, "latest.wav")
        writeWav(wavFile, pcmData, offset)
        return wavFile
    }

    private fun writeWav(file: File, pcmData: ByteArray, pcmLength: Int) {
        FileOutputStream(file).use { output ->
            output.write(wavHeader(pcmLength))
            output.write(pcmData, 0, pcmLength)
        }
    }

    private fun wavHeader(pcmLength: Int): ByteArray {
        val totalLength = pcmLength + 36
        val byteRate = sampleRate * 2
        val header = ByteBuffer.allocate(44).order(ByteOrder.LITTLE_ENDIAN)
        header.put("RIFF".toByteArray())
        header.putInt(totalLength)
        header.put("WAVE".toByteArray())
        header.put("fmt ".toByteArray())
        header.putInt(16)
        header.putShort(1.toShort())
        header.putShort(1.toShort())
        header.putInt(sampleRate)
        header.putInt(byteRate)
        header.putShort(2.toShort())
        header.putShort(16.toShort())
        header.put("data".toByteArray())
        header.putInt(pcmLength)
        return header.array()
    }
}
