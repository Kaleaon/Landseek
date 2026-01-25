/**
 * Chat UI State - Sealed class for managing chat states
 * Inspired by GPT Mobile's ApiState pattern for clean state management
 */

package com.landseek.aichat.ui.chat

/**
 * Represents the different states of the chat UI.
 * Uses sealed class pattern from GPT Mobile for type-safe state handling.
 */
sealed class ChatUiState {
    /**
     * Initial idle state - no activity
     */
    object Idle : ChatUiState()
    
    /**
     * Loading state - waiting for AI response
     */
    object Loading : ChatUiState()
    
    /**
     * Streaming state - AI is generating response in real-time
     * @param aiId The AI personality currently responding
     * @param partialContent The partial content received so far
     */
    data class Streaming(
        val aiId: String,
        val partialContent: String
    ) : ChatUiState()
    
    /**
     * Thinking state - AI is processing RAG/RLM context
     * @param aiId The AI personality currently thinking
     * @param thought Current thought or context retrieval status
     */
    data class Thinking(
        val aiId: String,
        val thought: String
    ) : ChatUiState()
    
    /**
     * Success state - messages loaded successfully
     * @param messages The list of chat messages
     */
    data class Success(
        val messages: List<ChatMessage>
    ) : ChatUiState()
    
    /**
     * Error state - something went wrong
     * @param message Error message to display
     * @param retryAction Optional retry action
     */
    data class Error(
        val message: String,
        val retryAction: (() -> Unit)? = null
    ) : ChatUiState()
}

/**
 * Actions available on chat messages (from GPT Mobile long-press pattern)
 */
enum class MessageAction {
    COPY,
    SELECT,
    RETRY,
    DELETE,
    REPLY
}
