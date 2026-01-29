package com.landseek.aichat.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.landseek.aichat.data.model.*
import com.landseek.aichat.data.repository.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import javax.inject.Inject

data class BackupData(
    val version: Int = 1,
    val timestamp: Long = System.currentTimeMillis(),
    val messages: List<MessageEntity>? = null,
    val aiStates: List<AIStateEntity>? = null,
    val conversations: List<PrivateConversationEntity>? = null,
    val settings: List<SettingsEntity>? = null,
    val documents: List<DocumentEntity>? = null
)

sealed class SettingsUiState {
    object Idle : SettingsUiState()
    object Loading : SettingsUiState()
    data class Success(val message: String) : SettingsUiState()
    data class Error(val message: String) : SettingsUiState()
}

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val messageRepository: MessageRepository,
    private val aiStateRepository: AIStateRepository,
    private val privateConversationRepository: PrivateConversationRepository,
    private val settingsRepository: SettingsRepository,
    private val documentRepository: DocumentRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow<SettingsUiState>(SettingsUiState.Idle)
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    suspend fun getExportDataJson(): String {
        return withContext(Dispatchers.IO) {
            val messages = messageRepository.getAllMessagesList()
            val aiStates = aiStateRepository.getAllStatesList()
            val conversations = privateConversationRepository.getAllConversationsList()
            val settings = settingsRepository.getAllSettingsList()
            val documents = documentRepository.getAllDocumentsList()

            val backup = BackupData(
                messages = messages,
                aiStates = aiStates,
                conversations = conversations,
                settings = settings,
                documents = documents
            )

            Gson().toJson(backup)
        }
    }

    fun importData(jsonString: String) {
        viewModelScope.launch {
            _uiState.value = SettingsUiState.Loading
            try {
                withContext(Dispatchers.IO) {
                    val backup = Gson().fromJson(jsonString, BackupData::class.java)

                    // We use insert(REPLACE) so existing records with same ID are updated.
                    // New records are inserted.

                    backup.messages?.let {
                        if (it.isNotEmpty()) messageRepository.insertMessages(it)
                    }

                    backup.aiStates?.let {
                        if (it.isNotEmpty()) aiStateRepository.insertAll(it)
                    }

                    // Private conversations - fetch doesn't have batch insert, iterate
                    backup.conversations?.forEach {
                        privateConversationRepository.insert(it)
                    }

                    // Settings - no batch insert exposed in Repo, iterate
                    backup.settings?.forEach {
                         settingsRepository.set(it.key, it.value)
                    }

                    // Documents - no batch insert, iterate
                    backup.documents?.forEach {
                        documentRepository.insert(it)
                    }
                }
                _uiState.value = SettingsUiState.Success("Data imported successfully")
            } catch (e: Exception) {
                _uiState.value = SettingsUiState.Error("Import failed: ${e.message}")
            }
        }
    }

    fun resetUiState() {
        _uiState.value = SettingsUiState.Idle
    }

    fun clearHistory() {
        viewModelScope.launch {
            _uiState.value = SettingsUiState.Loading
            try {
                // Delete all messages by passing a future timestamp
                messageRepository.deleteOldMessages(System.currentTimeMillis() + 1000)
                _uiState.value = SettingsUiState.Success("Chat history cleared")
            } catch (e: Exception) {
                _uiState.value = SettingsUiState.Error("Failed to clear history: ${e.message}")
            }
        }
    }
}
