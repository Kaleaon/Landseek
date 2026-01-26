/**
 * Model Download Manager - Easily download and manage AI models
 *
 * Provides functionality to:
 * - Download Gemma 3 models (4B, 1B variants)
 * - Download other supported models (Llama, Mistral, Phi, etc.)
 * - Verify model integrity
 * - Manage model storage
 * - Convert between formats (GGUF, ONNX, etc.)
 * 
 * Converted from Python: src/model_manager.py
 */

package com.landseek.aichat.domain.model

import kotlinx.serialization.Serializable

/**
 * Supported model formats
 */
enum class ModelFormat(val value: String) {
    GGUF("gguf"),              // llama.cpp format (recommended for mobile)
    ONNX("onnx"),              // ONNX format for broad compatibility
    SAFETENSORS("safetensors"), // HuggingFace format
    PYTORCH("pytorch"),        // PyTorch .pt/.bin format
    TFLITE("tflite")           // TensorFlow Lite (Android optimized)
}

/**
 * Model size categories
 */
enum class ModelSize(val value: String) {
    TINY("tiny"),              // < 500MB
    SMALL("small"),            // 500MB - 2GB
    MEDIUM("medium"),          // 2GB - 8GB
    LARGE("large")             // > 8GB
}

/**
 * Information about a downloadable model
 */
@Serializable
data class ModelInfo(
    val id: String,
    val name: String,
    val description: String,
    val sizeBytes: Long,
    val sizeCategory: ModelSize,
    val format: ModelFormat,
    val downloadUrl: String,
    val sha256: String? = null,
    val requiredRamMb: Int = 4096,
    val supportsTpu: Boolean = false,
    val supportsGpu: Boolean = true,
    val quantization: String? = null,
    val parameters: String? = null,
    val license: String = "Unknown",
    val homepage: String? = null,
    val tags: List<String> = emptyList()
) {
    /**
     * Human-readable size
     */
    val sizeHuman: String
        get() = when {
            sizeBytes < 1024 * 1024 -> "${"%.1f".format(sizeBytes / 1024.0)} KB"
            sizeBytes < 1024 * 1024 * 1024 -> "${"%.1f".format(sizeBytes / (1024.0 * 1024))} MB"
            else -> "${"%.2f".format(sizeBytes / (1024.0 * 1024 * 1024))} GB"
        }
}

/**
 * Available models catalog
 */
val MODEL_CATALOG: Map<String, ModelInfo> = mapOf(
    // Gemma 3 Models (Pixel TPU optimized)
    "gemma3-4b-gguf" to ModelInfo(
        id = "gemma3-4b-gguf",
        name = "Gemma 3 4B (GGUF Q4)",
        description = "Google's Gemma 3 4B model quantized for mobile. Best for Pixel 10 Pro TPU.",
        sizeBytes = 2_500_000_000L,  // ~2.5GB
        sizeCategory = ModelSize.MEDIUM,
        format = ModelFormat.GGUF,
        downloadUrl = "https://huggingface.co/google/gemma-3-4b-it-gguf/resolve/main/gemma-3-4b-it-q4_k_m.gguf",
        requiredRamMb = 4096,
        supportsTpu = true,
        supportsGpu = true,
        quantization = "Q4_K_M",
        parameters = "4B",
        license = "Gemma License",
        homepage = "https://ai.google.dev/gemma",
        tags = listOf("google", "gemma", "recommended", "pixel-tpu", "multimodal")
    ),
    "gemma3-4b-q8" to ModelInfo(
        id = "gemma3-4b-q8",
        name = "Gemma 3 4B (GGUF Q8)",
        description = "Higher quality quantization for better output. Requires more RAM.",
        sizeBytes = 4_200_000_000L,  // ~4.2GB
        sizeCategory = ModelSize.MEDIUM,
        format = ModelFormat.GGUF,
        downloadUrl = "https://huggingface.co/google/gemma-3-4b-it-gguf/resolve/main/gemma-3-4b-it-q8_0.gguf",
        requiredRamMb = 6144,
        supportsTpu = true,
        supportsGpu = true,
        quantization = "Q8_0",
        parameters = "4B",
        license = "Gemma License",
        homepage = "https://ai.google.dev/gemma",
        tags = listOf("google", "gemma", "high-quality", "pixel-tpu")
    ),
    "gemma3-1b-gguf" to ModelInfo(
        id = "gemma3-1b-gguf",
        name = "Gemma 3 1B (GGUF Q4)",
        description = "Lighter Gemma 3 variant. Good for older devices or faster inference.",
        sizeBytes = 800_000_000L,  // ~800MB
        sizeCategory = ModelSize.SMALL,
        format = ModelFormat.GGUF,
        downloadUrl = "https://huggingface.co/google/gemma-3-1b-it-gguf/resolve/main/gemma-3-1b-it-q4_k_m.gguf",
        requiredRamMb = 2048,
        supportsTpu = true,
        supportsGpu = true,
        quantization = "Q4_K_M",
        parameters = "1B",
        license = "Gemma License",
        homepage = "https://ai.google.dev/gemma",
        tags = listOf("google", "gemma", "lightweight", "fast")
    ),

    // Llama 3.2 Models
    "llama32-3b-gguf" to ModelInfo(
        id = "llama32-3b-gguf",
        name = "Llama 3.2 3B (GGUF Q4)",
        description = "Meta's Llama 3.2 3B model. Good general-purpose assistant.",
        sizeBytes = 1_900_000_000L,  // ~1.9GB
        sizeCategory = ModelSize.SMALL,
        format = ModelFormat.GGUF,
        downloadUrl = "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        requiredRamMb = 3072,
        supportsTpu = false,
        supportsGpu = true,
        quantization = "Q4_K_M",
        parameters = "3B",
        license = "Llama 3.2 Community License",
        homepage = "https://llama.meta.com/",
        tags = listOf("meta", "llama", "general-purpose")
    ),
    "llama32-1b-gguf" to ModelInfo(
        id = "llama32-1b-gguf",
        name = "Llama 3.2 1B (GGUF Q4)",
        description = "Smallest Llama 3.2 model. Very fast inference.",
        sizeBytes = 700_000_000L,  // ~700MB
        sizeCategory = ModelSize.SMALL,
        format = ModelFormat.GGUF,
        downloadUrl = "https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        requiredRamMb = 1536,
        supportsTpu = false,
        supportsGpu = true,
        quantization = "Q4_K_M",
        parameters = "1B",
        license = "Llama 3.2 Community License",
        homepage = "https://llama.meta.com/",
        tags = listOf("meta", "llama", "lightweight", "fast")
    ),

    // Phi Models
    "phi3-mini-gguf" to ModelInfo(
        id = "phi3-mini-gguf",
        name = "Phi-3 Mini (GGUF Q4)",
        description = "Microsoft's Phi-3 Mini. Excellent reasoning for its size.",
        sizeBytes = 2_300_000_000L,  // ~2.3GB
        sizeCategory = ModelSize.MEDIUM,
        format = ModelFormat.GGUF,
        downloadUrl = "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf",
        requiredRamMb = 4096,
        supportsTpu = false,
        supportsGpu = true,
        quantization = "Q4",
        parameters = "3.8B",
        license = "MIT",
        homepage = "https://azure.microsoft.com/en-us/products/phi-3",
        tags = listOf("microsoft", "phi", "reasoning", "coding")
    ),

    // Mistral Models
    "mistral-7b-gguf" to ModelInfo(
        id = "mistral-7b-gguf",
        name = "Mistral 7B (GGUF Q4)",
        description = "Mistral AI's 7B model. High quality but requires more resources.",
        sizeBytes = 4_100_000_000L,  // ~4.1GB
        sizeCategory = ModelSize.MEDIUM,
        format = ModelFormat.GGUF,
        downloadUrl = "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
        requiredRamMb = 6144,
        supportsTpu = false,
        supportsGpu = true,
        quantization = "Q4_K_M",
        parameters = "7B",
        license = "Apache 2.0",
        homepage = "https://mistral.ai/",
        tags = listOf("mistral", "high-quality", "multilingual")
    )
)

/**
 * Download progress callback interface
 */
interface DownloadProgressListener {
    fun onProgress(bytesDownloaded: Long, totalBytes: Long)
    fun onComplete(success: Boolean, filePath: String?, error: String?)
}

/**
 * Model Manager for handling model downloads and management
 */
class ModelManager(
    private val storageDir: String
) {
    private val downloadedModels: MutableMap<String, String> = mutableMapOf()

    /**
     * Get a model by ID from the catalog
     */
    fun getModelInfo(modelId: String): ModelInfo? = MODEL_CATALOG[modelId]

    /**
     * List all available models in the catalog
     */
    fun listAvailableModels(): List<ModelInfo> = MODEL_CATALOG.values.toList()

    /**
     * List models by tag
     */
    fun listModelsByTag(tag: String): List<ModelInfo> =
        MODEL_CATALOG.values.filter { tag in it.tags }

    /**
     * List models by size category
     */
    fun listModelsBySize(size: ModelSize): List<ModelInfo> =
        MODEL_CATALOG.values.filter { it.sizeCategory == size }

    /**
     * Check if a model is downloaded
     */
    fun isModelDownloaded(modelId: String): Boolean =
        modelId in downloadedModels

    /**
     * Get the path to a downloaded model
     */
    fun getModelPath(modelId: String): String? =
        downloadedModels[modelId]

    /**
     * Get recommended models for device
     */
    fun getRecommendedModels(
        availableRamMb: Int,
        hasTpu: Boolean = false,
        hasGpu: Boolean = true
    ): List<ModelInfo> {
        return MODEL_CATALOG.values.filter { model ->
            model.requiredRamMb <= availableRamMb &&
            (!hasTpu || model.supportsTpu) &&
            (!hasGpu || model.supportsGpu)
        }.sortedBy { it.requiredRamMb }
    }

    /**
     * Format model list for display
     */
    fun formatModelList(models: List<ModelInfo>): String {
        val sb = StringBuilder()
        sb.appendLine("Available Models:")
        sb.appendLine("=".repeat(50))
        
        for (model in models) {
            sb.appendLine()
            sb.appendLine("📦 ${model.name}")
            sb.appendLine("   ID: ${model.id}")
            sb.appendLine("   Size: ${model.sizeHuman}")
            sb.appendLine("   Format: ${model.format.value.uppercase()}")
            sb.appendLine("   RAM Required: ${model.requiredRamMb}MB")
            if (model.supportsTpu) sb.appendLine("   ⚡ TPU Supported")
            if (model.supportsGpu) sb.appendLine("   🎮 GPU Supported")
            sb.appendLine("   ${model.description}")
        }
        
        return sb.toString()
    }
}

/**
 * Get global model manager
 */
private var modelManagerInstance: ModelManager? = null

fun getModelManager(storageDir: String = ""): ModelManager {
    if (modelManagerInstance == null) {
        modelManagerInstance = ModelManager(storageDir)
    }
    return modelManagerInstance!!
}
