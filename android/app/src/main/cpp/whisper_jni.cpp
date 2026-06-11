#include <jni.h>
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#include "whisper.h"

namespace {

struct WavData {
    int sample_rate = 0;
    int channels = 0;
    int bits_per_sample = 0;
    std::vector<float> pcm_f32;
};

uint32_t read_u32_le(const uint8_t *p) {
    return static_cast<uint32_t>(p[0]) |
           (static_cast<uint32_t>(p[1]) << 8) |
           (static_cast<uint32_t>(p[2]) << 16) |
           (static_cast<uint32_t>(p[3]) << 24);
}

uint16_t read_u16_le(const uint8_t *p) {
    return static_cast<uint16_t>(p[0]) |
           (static_cast<uint16_t>(p[1]) << 8);
}

bool read_wav_file(const std::string &path, WavData &out, std::string &error) {
    std::ifstream file(path, std::ios::binary);
    if (!file) {
        error = "Cannot open WAV file: " + path;
        return false;
    }

    std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());
    if (bytes.size() < 44) {
        error = "WAV file is too small.";
        return false;
    }
    if (std::memcmp(bytes.data(), "RIFF", 4) != 0 || std::memcmp(bytes.data() + 8, "WAVE", 4) != 0) {
        error = "Only RIFF/WAVE files are supported.";
        return false;
    }

    size_t pos = 12;
    bool found_fmt = false;
    bool found_data = false;
    uint16_t audio_format = 0;
    const uint8_t *data_ptr = nullptr;
    uint32_t data_size = 0;

    while (pos + 8 <= bytes.size()) {
        const uint8_t *chunk = bytes.data() + pos;
        const uint32_t chunk_size = read_u32_le(chunk + 4);
        pos += 8;
        if (pos + chunk_size > bytes.size()) break;

        if (std::memcmp(chunk, "fmt ", 4) == 0 && chunk_size >= 16) {
            audio_format = read_u16_le(bytes.data() + pos);
            out.channels = read_u16_le(bytes.data() + pos + 2);
            out.sample_rate = static_cast<int>(read_u32_le(bytes.data() + pos + 4));
            out.bits_per_sample = read_u16_le(bytes.data() + pos + 14);
            found_fmt = true;
        } else if (std::memcmp(chunk, "data", 4) == 0) {
            data_ptr = bytes.data() + pos;
            data_size = chunk_size;
            found_data = true;
        }

        pos += chunk_size + (chunk_size % 2);
    }

    if (!found_fmt || !found_data) {
        error = "WAV file is missing fmt or data chunk.";
        return false;
    }
    if (audio_format != 1 || out.bits_per_sample != 16) {
        error = "Only 16-bit PCM WAV is supported by this Android scaffold.";
        return false;
    }
    if (out.channels <= 0) {
        error = "Invalid channel count in WAV file.";
        return false;
    }
    if (out.sample_rate != 16000) {
        error = "Expected 16 kHz WAV. Use AudioRecorder or scripts/prepare_sample_audio.sh.";
        return false;
    }

    const int sample_count = static_cast<int>(data_size / 2 / out.channels);
    out.pcm_f32.reserve(sample_count);
    const auto *samples = reinterpret_cast<const int16_t *>(data_ptr);
    for (int i = 0; i < sample_count; ++i) {
        int32_t sum = 0;
        for (int ch = 0; ch < out.channels; ++ch) {
            sum += samples[i * out.channels + ch];
        }
        const float mono = static_cast<float>(sum) / static_cast<float>(out.channels) / 32768.0f;
        out.pcm_f32.push_back(mono);
    }
    return true;
}

std::string jstring_to_string(JNIEnv *env, jstring value) {
    const char *chars = env->GetStringUTFChars(value, nullptr);
    std::string result(chars == nullptr ? "" : chars);
    env->ReleaseStringUTFChars(value, chars);
    return result;
}

}  // namespace

extern "C" JNIEXPORT jlong JNICALL
Java_com_example_asrmobile_WhisperEngine_initModel(
        JNIEnv *env,
        jobject,
        jstring modelPath) {
    const std::string path = jstring_to_string(env, modelPath);
    whisper_context_params cparams = whisper_context_default_params();
    cparams.use_gpu = false;

    whisper_context *ctx = whisper_init_from_file_with_params(path.c_str(), cparams);
    return reinterpret_cast<jlong>(ctx);
}

extern "C" JNIEXPORT jstring JNICALL
Java_com_example_asrmobile_WhisperEngine_transcribeFromFile(
        JNIEnv *env,
        jobject,
        jlong handle,
        jstring wavPath) {
    auto *ctx = reinterpret_cast<whisper_context *>(handle);
    if (ctx == nullptr) {
        return env->NewStringUTF("Model is not loaded or native context is invalid.");
    }

    const std::string path = jstring_to_string(env, wavPath);
    WavData wav;
    std::string error;
    if (!read_wav_file(path, wav, error)) {
        return env->NewStringUTF(error.c_str());
    }

    whisper_full_params params = whisper_full_default_params(WHISPER_SAMPLING_GREEDY);
    params.n_threads = std::max(1u, std::min(4u, std::thread::hardware_concurrency()));
    params.translate = false;
    params.no_context = true;
    params.no_timestamps = true;
    params.print_progress = false;
    params.print_realtime = false;
    params.print_timestamps = false;
    params.language = "auto";

    if (whisper_full(ctx, params, wav.pcm_f32.data(), static_cast<int>(wav.pcm_f32.size())) != 0) {
        return env->NewStringUTF("whisper_full failed during transcription.");
    }

    std::ostringstream transcript;
    const int n_segments = whisper_full_n_segments(ctx);
    for (int i = 0; i < n_segments; ++i) {
        const char *text = whisper_full_get_segment_text(ctx, i);
        if (text != nullptr) transcript << text;
    }

    const std::string result = transcript.str();
    return env->NewStringUTF(result.empty() ? "[No speech recognized]" : result.c_str());
}

extern "C" JNIEXPORT void JNICALL
Java_com_example_asrmobile_WhisperEngine_releaseModel(
        JNIEnv *,
        jobject,
        jlong handle) {
    auto *ctx = reinterpret_cast<whisper_context *>(handle);
    if (ctx != nullptr) whisper_free(ctx);
}
