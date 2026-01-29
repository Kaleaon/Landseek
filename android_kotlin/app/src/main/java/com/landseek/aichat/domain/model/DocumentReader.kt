/**
 * Document Reader - Multi-format Document Processing
 *
 * Supports reading various document formats for AI processing:
 * - Plain text files (.txt, .md, .csv, .json, .xml, .yaml, etc.)
 * - PDF documents (.pdf)
 * - Microsoft Word documents (.docx, .doc)
 * - HTML files and web links
 * - Images (.jpg, .jpeg, .png, .gif, .webp) - Gemma 3 multimodal
 * - Audio files (.mp3, .wav, .ogg) - metadata extraction
 * - Video files (.mp4, .webm) - metadata extraction
 *
 * Gemma 3 4B is multimodal and can process:
 * - Text (128K token context window)
 * - Images (JPEG/PNG, normalized to 896x896)
 *
 * Converted from Python: src/document_reader.py
 */

package com.landseek.aichat.domain.model

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.util.Base64
import kotlinx.serialization.Serializable
import java.io.*
import java.net.URL
import java.time.Instant
import org.apache.poi.xwpf.usermodel.XWPFDocument

/**
 * Supported file extensions and their MIME types.
 */
val SUPPORTED_EXTENSIONS: Map<String, String> = mapOf(
    // Plain text formats
    ".txt" to "text/plain",
    ".md" to "text/markdown",
    ".markdown" to "text/markdown",
    ".rst" to "text/x-rst",
    ".csv" to "text/csv",
    ".tsv" to "text/tab-separated-values",
    ".json" to "application/json",
    ".xml" to "text/xml",
    ".html" to "text/html",
    ".htm" to "text/html",
    ".yaml" to "text/yaml",
    ".yml" to "text/yaml",
    ".toml" to "text/toml",
    ".ini" to "text/plain",
    ".cfg" to "text/plain",
    ".conf" to "text/plain",
    ".log" to "text/plain",
    
    // Code files
    ".py" to "text/x-python",
    ".js" to "text/javascript",
    ".ts" to "text/typescript",
    ".java" to "text/x-java",
    ".kt" to "text/x-kotlin",
    ".c" to "text/x-c",
    ".cpp" to "text/x-c++",
    ".h" to "text/x-c",
    ".cs" to "text/x-csharp",
    ".go" to "text/x-go",
    ".rs" to "text/x-rust",
    ".rb" to "text/x-ruby",
    ".php" to "text/x-php",
    ".swift" to "text/x-swift",
    ".sql" to "text/x-sql",
    ".sh" to "text/x-shellscript",
    ".bash" to "text/x-shellscript",
    
    // Document formats
    ".pdf" to "application/pdf",
    ".docx" to "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc" to "application/msword",
    ".odt" to "application/vnd.oasis.opendocument.text",
    ".rtf" to "application/rtf",
    
    // Image formats (Gemma 3 multimodal)
    ".jpg" to "image/jpeg",
    ".jpeg" to "image/jpeg",
    ".png" to "image/png",
    ".gif" to "image/gif",
    ".webp" to "image/webp",
    ".bmp" to "image/bmp",
    
    // Audio formats
    ".mp3" to "audio/mpeg",
    ".wav" to "audio/wav",
    ".ogg" to "audio/ogg",
    ".flac" to "audio/flac",
    ".m4a" to "audio/mp4",
    
    // Video formats
    ".mp4" to "video/mp4",
    ".webm" to "video/webm",
    ".mkv" to "video/x-matroska",
    ".avi" to "video/x-msvideo",
    ".mov" to "video/quicktime"
)

/**
 * Categories for format grouping.
 */
val FORMAT_CATEGORIES: Map<String, List<String>> = mapOf(
    "text" to listOf(".txt", ".md", ".markdown", ".rst"),
    "data" to listOf(".json", ".csv", ".tsv", ".xml", ".yaml", ".yml", ".toml"),
    "code" to listOf(".py", ".js", ".ts", ".java", ".kt", ".c", ".cpp", ".cs", 
                     ".go", ".rs", ".rb", ".php", ".swift", ".sql", ".sh"),
    "documents" to listOf(".pdf", ".docx", ".doc", ".odt", ".rtf"),
    "web" to listOf(".html", ".htm"),
    "images" to listOf(".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"),
    "audio" to listOf(".mp3", ".wav", ".ogg", ".flac", ".m4a"),
    "video" to listOf(".mp4", ".webm", ".mkv", ".avi", ".mov"),
    "config" to listOf(".ini", ".cfg", ".conf", ".log")
)

/**
 * Represents extracted document content.
 */
@Serializable
data class DocumentContent(
    val text: String,
    val title: String? = null,
    val author: String? = null,
    val metadata: Map<String, String> = emptyMap(),
    val pages: Int = 1,
    val wordCount: Int = text.split(Regex("\\s+")).filter { it.isNotEmpty() }.size,
    val charCount: Int = text.length,
    val sourceType: String = "file",  // file, url, text
    val originalFormat: String = "text",
    // For multimodal content
    val imageBase64: String? = null,  // Base64 encoded image for Gemma vision
    val isMultimodal: Boolean = false,
    val extractedAt: String = Instant.now().toString()
)

/**
 * Result from reading a document.
 */
sealed class DocumentReadResult {
    data class Success(val content: DocumentContent) : DocumentReadResult()
    data class Error(val message: String) : DocumentReadResult()
}

/**
 * Document Reader for multi-format document processing.
 */
class DocumentReader(private val context: Context? = null) {
    
    companion object {
        // Maximum image dimension for Gemma 3 (normalized to 896x896)
        const val MAX_IMAGE_DIMENSION = 896
        
        // Maximum text size (128K tokens ~ 512K characters)
        const val MAX_TEXT_SIZE = 512_000
    }
    
    /**
     * Read a document from a file path.
     */
    fun readFile(filePath: String): DocumentReadResult {
        return try {
            val file = File(filePath)
            if (!file.exists()) {
                return DocumentReadResult.Error("File not found: $filePath")
            }
            
            val extension = "." + file.extension.lowercase()
            val mimeType = SUPPORTED_EXTENSIONS[extension]
                ?: return DocumentReadResult.Error("Unsupported file format: $extension")
            
            readFileByMimeType(file, mimeType, extension)
        } catch (e: Exception) {
            DocumentReadResult.Error("Error reading file: ${e.message}")
        }
    }
    
    /**
     * Read a document from a URI (Android content:// or file://).
     */
    fun readUri(uri: Uri): DocumentReadResult {
        if (context == null) {
            return DocumentReadResult.Error("Context required for URI reading")
        }
        
        return try {
            val inputStream = context.contentResolver.openInputStream(uri)
                ?: return DocumentReadResult.Error("Cannot open URI: $uri")
            
            val mimeType = context.contentResolver.getType(uri) ?: "text/plain"
            val fileName = uri.lastPathSegment ?: "unknown"
            val extension = "." + fileName.substringAfterLast('.', "txt").lowercase()
            
            inputStream.use { stream ->
                readStreamByMimeType(stream, mimeType, extension, fileName)
            }
        } catch (e: Exception) {
            DocumentReadResult.Error("Error reading URI: ${e.message}")
        }
    }
    
    /**
     * Read a document from a URL.
     */
    fun readUrl(urlString: String): DocumentReadResult {
        return try {
            val url = URL(urlString)
            val connection = url.openConnection()
            connection.connectTimeout = 10_000
            connection.readTimeout = 30_000
            
            val mimeType = connection.contentType?.split(";")?.first() ?: "text/html"
            val fileName = url.path.substringAfterLast('/')
            val extension = "." + fileName.substringAfterLast('.', "html").lowercase()
            
            connection.getInputStream().use { stream ->
                readStreamByMimeType(stream, mimeType, extension, fileName, urlString)
            }
        } catch (e: Exception) {
            DocumentReadResult.Error("Error reading URL: ${e.message}")
        }
    }
    
    /**
     * Read plain text content.
     */
    fun readText(text: String, title: String? = null): DocumentReadResult {
        if (text.length > MAX_TEXT_SIZE) {
            return DocumentReadResult.Error("Text too large (max ${MAX_TEXT_SIZE} characters)")
        }
        
        return DocumentReadResult.Success(
            DocumentContent(
                text = text,
                title = title,
                sourceType = "text",
                originalFormat = "text"
            )
        )
    }
    
    /**
     * Read and encode an image for Gemma 3 multimodal processing.
     */
    fun readImage(filePath: String): DocumentReadResult {
        return try {
            val file = File(filePath)
            if (!file.exists()) {
                return DocumentReadResult.Error("Image not found: $filePath")
            }
            
            val bitmap = BitmapFactory.decodeFile(filePath)
                ?: return DocumentReadResult.Error("Cannot decode image: $filePath")
            
            processImageBitmap(bitmap, file.name)
        } catch (e: Exception) {
            DocumentReadResult.Error("Error reading image: ${e.message}")
        }
    }
    
    /**
     * Read and encode an image from bytes.
     */
    fun readImageBytes(bytes: ByteArray, fileName: String = "image"): DocumentReadResult {
        return try {
            val bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
                ?: return DocumentReadResult.Error("Cannot decode image bytes")
            
            processImageBitmap(bitmap, fileName)
        } catch (e: Exception) {
            DocumentReadResult.Error("Error reading image bytes: ${e.message}")
        }
    }
    
    /**
     * Check if a file extension is supported.
     */
    fun isSupported(extension: String): Boolean {
        val ext = if (extension.startsWith(".")) extension else ".$extension"
        return SUPPORTED_EXTENSIONS.containsKey(ext.lowercase())
    }
    
    /**
     * Get the category of a file extension.
     */
    fun getCategory(extension: String): String? {
        val ext = if (extension.startsWith(".")) extension else ".$extension"
        return FORMAT_CATEGORIES.entries.find { ext.lowercase() in it.value }?.key
    }
    
    /**
     * Get supported extensions for a category.
     */
    fun getExtensionsForCategory(category: String): List<String> {
        return FORMAT_CATEGORIES[category] ?: emptyList()
    }
    
    // Private helper methods
    
    private fun readFileByMimeType(
        file: File,
        mimeType: String,
        extension: String
    ): DocumentReadResult {
        return when {
            mimeType.startsWith("text/") || mimeType == "application/json" -> {
                readTextFile(file, extension)
            }
            mimeType.startsWith("image/") -> {
                readImageFile(file)
            }
            mimeType == "application/pdf" -> {
                readPdfFile(file)
            }
            mimeType.contains("wordprocessingml") || mimeType == "application/msword" -> {
                readDocxFile(file)
            }
            else -> {
                // Try to read as text
                readTextFile(file, extension)
            }
        }
    }
    
    private fun readStreamByMimeType(
        stream: InputStream,
        mimeType: String,
        extension: String,
        fileName: String,
        source: String? = null
    ): DocumentReadResult {
        return when {
            mimeType.startsWith("text/") || mimeType == "application/json" -> {
                readTextStream(stream, extension, fileName, source)
            }
            mimeType.startsWith("image/") -> {
                readImageStream(stream, fileName)
            }
            mimeType == "text/html" || extension == ".html" || extension == ".htm" -> {
                readHtmlStream(stream, fileName, source)
            }
            else -> {
                // Try to read as text
                readTextStream(stream, extension, fileName, source)
            }
        }
    }
    
    private fun readTextFile(file: File, extension: String): DocumentReadResult {
        return try {
            val text = file.readText()
            if (text.length > MAX_TEXT_SIZE) {
                return DocumentReadResult.Error("File too large (max ${MAX_TEXT_SIZE} characters)")
            }
            
            DocumentReadResult.Success(
                DocumentContent(
                    text = text,
                    title = file.nameWithoutExtension,
                    sourceType = "file",
                    originalFormat = extension.trimStart('.'),
                    metadata = mapOf(
                        "path" to file.absolutePath,
                        "size" to file.length().toString(),
                        "lastModified" to Instant.ofEpochMilli(file.lastModified()).toString()
                    )
                )
            )
        } catch (e: Exception) {
            DocumentReadResult.Error("Error reading text file: ${e.message}")
        }
    }
    
    private fun readTextStream(
        stream: InputStream,
        extension: String,
        fileName: String,
        source: String?
    ): DocumentReadResult {
        return try {
            val text = stream.bufferedReader().readText()
            if (text.length > MAX_TEXT_SIZE) {
                return DocumentReadResult.Error("Content too large (max ${MAX_TEXT_SIZE} characters)")
            }
            
            val metadata = mutableMapOf<String, String>()
            source?.let { metadata["source"] = it }
            
            DocumentReadResult.Success(
                DocumentContent(
                    text = text,
                    title = fileName,
                    sourceType = if (source?.startsWith("http") == true) "url" else "file",
                    originalFormat = extension.trimStart('.'),
                    metadata = metadata
                )
            )
        } catch (e: Exception) {
            DocumentReadResult.Error("Error reading stream: ${e.message}")
        }
    }
    
    private fun readImageFile(file: File): DocumentReadResult {
        return try {
            val bitmap = BitmapFactory.decodeFile(file.absolutePath)
                ?: return DocumentReadResult.Error("Cannot decode image: ${file.name}")
            
            processImageBitmap(bitmap, file.name, file.absolutePath)
        } catch (e: Exception) {
            DocumentReadResult.Error("Error reading image: ${e.message}")
        }
    }
    
    private fun readImageStream(stream: InputStream, fileName: String): DocumentReadResult {
        return try {
            val bitmap = BitmapFactory.decodeStream(stream)
                ?: return DocumentReadResult.Error("Cannot decode image stream")
            
            processImageBitmap(bitmap, fileName)
        } catch (e: Exception) {
            DocumentReadResult.Error("Error reading image stream: ${e.message}")
        }
    }
    
    private fun processImageBitmap(
        bitmap: Bitmap,
        fileName: String,
        filePath: String? = null
    ): DocumentReadResult {
        return try {
            // Resize if needed for Gemma 3 (896x896)
            val resized = if (bitmap.width > MAX_IMAGE_DIMENSION || bitmap.height > MAX_IMAGE_DIMENSION) {
                val scale = MAX_IMAGE_DIMENSION.toFloat() / maxOf(bitmap.width, bitmap.height)
                Bitmap.createScaledBitmap(
                    bitmap,
                    (bitmap.width * scale).toInt(),
                    (bitmap.height * scale).toInt(),
                    true
                )
            } else {
                bitmap
            }
            
            // Convert to base64
            val outputStream = ByteArrayOutputStream()
            resized.compress(Bitmap.CompressFormat.JPEG, 85, outputStream)
            val base64 = Base64.encodeToString(outputStream.toByteArray(), Base64.NO_WRAP)
            
            val metadata = mutableMapOf(
                "width" to resized.width.toString(),
                "height" to resized.height.toString(),
                "originalWidth" to bitmap.width.toString(),
                "originalHeight" to bitmap.height.toString()
            )
            filePath?.let { metadata["path"] = it }
            
            DocumentReadResult.Success(
                DocumentContent(
                    text = "[Image: $fileName (${resized.width}x${resized.height})]",
                    title = fileName,
                    sourceType = "file",
                    originalFormat = "image",
                    imageBase64 = base64,
                    isMultimodal = true,
                    metadata = metadata
                )
            )
        } catch (e: Exception) {
            DocumentReadResult.Error("Error processing image: ${e.message}")
        }
    }
    
    private fun readPdfFile(file: File): DocumentReadResult {
        // TODO: Implement PDF text extraction using com.tom_roush:pdfbox-android
        // Add dependency: implementation("com.tom-roush:pdfbox-android:2.0.27.0")
        // Usage: PDDocument.load(file) -> pdfStripper.getText(document)
        return try {
            val metadata = mapOf(
                "path" to file.absolutePath,
                "size" to file.length().toString()
            )
            
            DocumentReadResult.Success(
                DocumentContent(
                    text = "[PDF Document: ${file.name}]\n\n⚠️ PDF text extraction requires pdfbox-android library. Add 'com.tom-roush:pdfbox-android:2.0.27.0' to dependencies.",
                    title = file.nameWithoutExtension,
                    sourceType = "file",
                    originalFormat = "pdf",
                    metadata = metadata
                )
            )
        } catch (e: Exception) {
            DocumentReadResult.Error("Error reading PDF: ${e.message}")
        }
    }
    
    private fun readDocxFile(file: File): DocumentReadResult {
        return try {
            FileInputStream(file).use { fis ->
                XWPFDocument(fis).use { document ->
                    val textBuilder = StringBuilder()

                    // Iterate paragraphs
                    for (paragraph in document.paragraphs) {
                        textBuilder.append(paragraph.text).append("\n")
                    }

                    val text = textBuilder.toString().trim()

                    if (text.length > MAX_TEXT_SIZE) {
                        return DocumentReadResult.Error("Document too large (max $MAX_TEXT_SIZE characters)")
                    }

                    val metadata = mapOf(
                        "path" to file.absolutePath,
                        "size" to file.length().toString(),
                        "lastModified" to Instant.ofEpochMilli(file.lastModified()).toString()
                    )

                    DocumentReadResult.Success(
                        DocumentContent(
                            text = text,
                            title = file.nameWithoutExtension,
                            sourceType = "file",
                            originalFormat = "docx",
                            metadata = metadata
                        )
                    )
                }
            }
        } catch (e: Exception) {
            DocumentReadResult.Error("Error reading DOCX: ${e.message}")
        }
    }
    
    private fun readHtmlStream(
        stream: InputStream,
        fileName: String,
        source: String?
    ): DocumentReadResult {
        return try {
            val html = stream.bufferedReader().readText()
            
            // Simple HTML to text conversion (strip tags)
            val text = html
                .replace(Regex("<script[^>]*>.*?</script>", RegexOption.DOT_MATCHES_ALL), "")
                .replace(Regex("<style[^>]*>.*?</style>", RegexOption.DOT_MATCHES_ALL), "")
                .replace(Regex("<[^>]+>"), " ")
                .replace(Regex("&nbsp;"), " ")
                .replace(Regex("&lt;"), "<")
                .replace(Regex("&gt;"), ">")
                .replace(Regex("&amp;"), "&")
                .replace(Regex("\\s+"), " ")
                .trim()
            
            // Extract title
            val titleMatch = Regex("<title[^>]*>([^<]+)</title>").find(html)
            val title = titleMatch?.groupValues?.get(1)?.trim() ?: fileName
            
            val metadata = mutableMapOf<String, String>()
            source?.let { metadata["source"] = it }
            
            DocumentReadResult.Success(
                DocumentContent(
                    text = text,
                    title = title,
                    sourceType = if (source?.startsWith("http") == true) "url" else "file",
                    originalFormat = "html",
                    metadata = metadata
                )
            )
        } catch (e: Exception) {
            DocumentReadResult.Error("Error reading HTML: ${e.message}")
        }
    }
}

/**
 * Get the global document reader instance.
 */
private var documentReaderInstance: DocumentReader? = null

fun getDocumentReader(context: Context? = null): DocumentReader {
    if (documentReaderInstance == null) {
        documentReaderInstance = DocumentReader(context)
    }
    return documentReaderInstance!!
}
