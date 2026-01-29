/**
 * Settings ViewModel - Manages settings screen logic
 */

package com.landseek.aichat.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.landseek.aichat.data.repository.MessageRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val messageRepository: MessageRepository
) : ViewModel() {

    fun clearHistory() {
        viewModelScope.launch {
            messageRepository.deleteAllMessages()
        }
    }
}
