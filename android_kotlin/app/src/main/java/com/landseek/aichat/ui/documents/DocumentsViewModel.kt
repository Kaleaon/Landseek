/**
 * Documents ViewModel - Manages document operations
 */

package com.landseek.aichat.ui.documents

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.landseek.aichat.data.model.DocumentEntity
import com.landseek.aichat.data.repository.AIStateRepository
import com.landseek.aichat.data.repository.DocumentRepository
import com.landseek.aichat.domain.model.DocumentReadResult
import com.landseek.aichat.domain.model.DocumentReader
import com.landseek.aichat.domain.model.RAGManager
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import javax.inject.Inject

@HiltViewModel
class DocumentsViewModel @Inject constructor(
    private val documentRepository: DocumentRepository,
    private val aiStateRepository: AIStateRepository,
    private val ragManager: RAGManager,
    private val documentReader: DocumentReader,
    @ApplicationContext private val context: Context
) : ViewModel() {

    val documents: StateFlow<List<DocumentEntity>> = documentRepository.getAllDocuments()
        .stateIn(viewModelScope, SharingStarted.Lazily, emptyList())

    private val _snackbarMessage = MutableSharedFlow<String>()
    val snackbarMessage = _snackbarMessage.asSharedFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    fun uploadDocument(uri: Uri) {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                val fileInfo = getFileInfo(uri) ?: return@launch
                val internalFile = copyFileToInternalStorage(uri, fileInfo.name)

                if (internalFile != null) {
                    val document = DocumentEntity(
                        name = fileInfo.name,
                        path = internalFile.absolutePath,
                        mimeType = fileInfo.mimeType,
                        sizeBytes = fileInfo.size,
                        uploadedAt = System.currentTimeMillis()
                    )
                    documentRepository.insert(document)
                    _snackbarMessage.emit("Uploaded ${fileInfo.name}")
                } else {
                    _snackbarMessage.emit("Failed to save file locally")
                }
            } catch (e: Exception) {
                _snackbarMessage.emit("Error uploading document: ${e.message}")
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun analyzeDocument(document: DocumentEntity) {
        viewModelScope.launch {
            _isLoading.value = true
            try {
                // Read content
                val result = withContext(Dispatchers.IO) {
                    documentReader.readFile(document.path)
                }

                when (result) {
                    is DocumentReadResult.Success -> {
                        val content = result.content.text
                        if (content.isBlank()) {
                            _snackbarMessage.emit("Document appears to be empty.")
                            return@launch
                        }

                        val activeAIs = aiStateRepository.getActiveStates().first()
                        if (activeAIs.isEmpty()) {
                            _snackbarMessage.emit("No active AIs found. Enable an AI to analyze.")
                            return@launch
                        }

                        var count = 0
                        withContext(Dispatchers.IO) {
                            activeAIs.forEach { ai ->
                                ragManager.getStore(ai.aiId).addDocument(
                                    content = content,
                                    source = document.path,
                                    sourceType = "document",
                                    metadata = mapOf(
                                        "name" to document.name,
                                        "mimeType" to document.mimeType,
                                        "id" to document.id.toString()
                                    )
                                )
                                count++
                            }
                        }
                        _snackbarMessage.emit("Analyzed and added to $count AI knowledge base(s).")
                    }
                    is DocumentReadResult.Error -> {
                        _snackbarMessage.emit("Failed to read document: ${result.message}")
                    }
                }
            } catch (e: Exception) {
                _snackbarMessage.emit("Error during analysis: ${e.message}")
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun deleteDocument(document: DocumentEntity) {
        viewModelScope.launch {
            try {
                documentRepository.delete(document)
                // Optionally delete the file
                val file = File(document.path)
                if (file.exists()) {
                    file.delete()
                }
                _snackbarMessage.emit("Deleted ${document.name}")
            } catch (e: Exception) {
                _snackbarMessage.emit("Error deleting document: ${e.message}")
            }
        }
    }

    private suspend fun copyFileToInternalStorage(uri: Uri, fileName: String): File? {
        return withContext(Dispatchers.IO) {
            try {
                val documentsDir = File(context.filesDir, "documents")
                if (!documentsDir.exists()) {
                    documentsDir.mkdirs()
                }

                // Ensure unique filename
                var finalFileName = fileName
                var file = File(documentsDir, finalFileName)
                var count = 1
                while (file.exists()) {
                    val nameWithoutExt = fileName.substringBeforeLast('.')
                    val ext = fileName.substringAfterLast('.', "")
                    val extStr = if (ext.isNotEmpty()) ".$ext" else ""
                    finalFileName = "${nameWithoutExt}_$count$extStr"
                    file = File(documentsDir, finalFileName)
                    count++
                }

                context.contentResolver.openInputStream(uri)?.use { input ->
                    FileOutputStream(file).use { output ->
                        input.copyTo(output)
                    }
                }
                file
            } catch (e: Exception) {
                e.printStackTrace()
                null
            }
        }
    }

    private data class FileInfo(val name: String, val size: Long, val mimeType: String)

    private fun getFileInfo(uri: Uri): FileInfo? {
        var name = "unknown_file"
        var size = 0L
        var mimeType = "application/octet-stream"

        try {
            val cursor = context.contentResolver.query(uri, null, null, null, null)
            cursor?.use {
                if (it.moveToFirst()) {
                    val nameIndex = it.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                    val sizeIndex = it.getColumnIndex(OpenableColumns.SIZE)

                    if (nameIndex != -1) name = it.getString(nameIndex)
                    if (sizeIndex != -1) size = it.getLong(sizeIndex)
                }
            }
            mimeType = context.contentResolver.getType(uri) ?: mimeType
        } catch (e: Exception) {
            e.printStackTrace()
            return null
        }

        return FileInfo(name, size, mimeType)
    }
}
