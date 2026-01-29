/**
 * Chat ViewModel - Manages chat state and logic
 * Enhanced with GPT Mobile patterns:
 * - ChatUiState sealed class for clean state management
 * - Streaming support with partial content
 * - ThinkingBlock state for RAG/RLM status
 */

package com.landseek.aichat.ui.chat

import androidx.compose.ui.graphics.Color
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.landseek.aichat.data.repository.MessageRepository
import com.landseek.aichat.data.repository.AIStateRepository
import com.landseek.aichat.domain.model.BUILTIN_PERSONALITIES
import com.landseek.aichat.ui.theme.AIColors
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.util.*
import javax.inject.Inject

/**
 * Streaming configuration constants
 * Extracted for maintainability (addresses code review feedback)
 */
private object StreamingConfig {
    const val THINKING_PHASE_DELAY_MS = 300L
    const val FORMULATING_DELAY_MS = 200L
    const val SENTENCE_END_DELAY_MS = 100L  // After . ! ?
    const val CLAUSE_DELAY_MS = 50L         // After , ; :
    const val WORD_DELAY_MS = 20L           // After space
    const val CHARACTER_DELAY_MS = 15L      // Default
    const val MESSAGE_GAP_DELAY_MS = 200L   // Between AI responses
}

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val messageRepository: MessageRepository,
    private val aiStateRepository: AIStateRepository
) : ViewModel() {
    
    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()
    
    private val _activeAIs = MutableStateFlow<List<ActiveAI>>(emptyList())
    val activeAIs: StateFlow<List<ActiveAI>> = _activeAIs.asStateFlow()
    
    private val _inputText = MutableStateFlow("")
    val inputText: StateFlow<String> = _inputText.asStateFlow()
    
    private val _isProcessing = MutableStateFlow(false)
    val isProcessing: StateFlow<Boolean> = _isProcessing.asStateFlow()
    
    // GPT Mobile pattern: ChatUiState for clean state management
    private val _uiState = MutableStateFlow<ChatUiState>(ChatUiState.Idle)
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()
    
    // Current AI thought/reasoning for ThinkingBlock
    private val _currentThought = MutableStateFlow("")
    val currentThought: StateFlow<String> = _currentThought.asStateFlow()
    
    init {
        initializeDefaultAIs()
        loadWelcomeMessages()
    }
    
    private fun initializeDefaultAIs() {
        val defaultAIs = BUILTIN_PERSONALITIES.take(3).map { p ->
            ActiveAI(
                id = p.name.lowercase(),
                name = p.name,
                avatar = p.avatar,
                isActive = true
            )
        }
        _activeAIs.value = defaultAIs
    }
    
    private fun loadWelcomeMessages() {
        val welcomeMessages = listOf(
            ChatMessage(
                sender = "System",
                avatar = "🤖",
                content = "Welcome to AI Chat Room! 🎉 You're chatting with AI personalities powered by Gemma 3 4B.",
                isUser = false,
                senderColor = Color.Gray
            ),
            ChatMessage(
                sender = "Nova",
                avatar = "🌟",
                content = "Hello! I'm Nova, curious and analytical. I love exploring ideas deeply. What would you like to discuss today?",
                isUser = false,
                senderColor = AIColors.getColorForAI("nova")
            ),
            ChatMessage(
                sender = "Echo",
                avatar = "🎭",
                content = "Hey there! I'm Echo, the creative spirit of our group. Think of me as your friendly muse! 🎨",
                isUser = false,
                senderColor = AIColors.getColorForAI("echo")
            ),
            ChatMessage(
                sender = "Sage",
                avatar = "🦉",
                content = "Greetings, seeker of wisdom. I am Sage, here to offer balanced perspectives and thoughtful insights.",
                isUser = false,
                senderColor = AIColors.getColorForAI("sage")
            )
        )
        _messages.value = welcomeMessages
    }
    
    fun onInputTextChange(text: String) {
        _inputText.value = text
    }
    
    fun sendMessage() {
        val text = _inputText.value.trim()
        if (text.isBlank() || _isProcessing.value) return
        
        viewModelScope.launch {
            _isProcessing.value = true
            _uiState.value = ChatUiState.Loading
            _inputText.value = ""
            
            // Add user message
            val userMessage = ChatMessage(
                sender = "You",
                avatar = "👤",
                content = text,
                isUser = true,
                senderColor = Color.White
            )
            _messages.value = _messages.value + userMessage
            
            // Simulate AI responses with streaming and thinking
            simulateAIResponses(text)
            
            _isProcessing.value = false
            _uiState.value = ChatUiState.Idle
            _currentThought.value = ""
        }
    }
    
    private suspend fun simulateAIResponses(userText: String) {
        val activeAIList = _activeAIs.value.filter { it.isActive }
        
        for (ai in activeAIList) {
            simulateSingleAIResponse(ai, userText)
        }
    }

    private suspend fun simulateSingleAIResponse(ai: ActiveAI, userText: String) {
        // Phase 1: Thinking/RAG retrieval (GPT Mobile ThinkingBlock pattern)
        _uiState.value = ChatUiState.Thinking(ai.id, "Retrieving context...")
        _currentThought.value = "🔍 ${ai.name} is searching knowledge base..."
        kotlinx.coroutines.delay(StreamingConfig.THINKING_PHASE_DELAY_MS)

        _currentThought.value = "📚 ${ai.name} is processing relevant context..."
        kotlinx.coroutines.delay(StreamingConfig.THINKING_PHASE_DELAY_MS)

        _currentThought.value = "💭 ${ai.name} is formulating response..."
        kotlinx.coroutines.delay(StreamingConfig.FORMULATING_DELAY_MS)

        // Phase 2: Generate response with streaming simulation
        val fullResponse = generateAIResponse(ai, userText)

        // Add message with loading state (shows ● cursor)
        val messageId = UUID.randomUUID().toString()
        val loadingMessage = ChatMessage(
            id = messageId,
            sender = ai.name,
            avatar = ai.avatar,
            content = "",
            isUser = false,
            senderColor = AIColors.getColorForAI(ai.id),
            isLoading = true,
            thoughts = "Processing with RAG context...",
            canRetry = true
        )
        _messages.value = _messages.value + loadingMessage
        _uiState.value = ChatUiState.Streaming(ai.id, "")

        // Phase 3: Stream response character by character (GPT Mobile pattern)
        var streamedContent = ""
        for (char in fullResponse) {
            streamedContent += char
            _uiState.value = ChatUiState.Streaming(ai.id, streamedContent)

            // Update message with partial content
            _messages.value = _messages.value.map { msg ->
                if (msg.id == messageId) {
                    msg.copy(content = streamedContent, isLoading = true)
                } else msg
            }

            // Variable delay for natural feel (using config constants)
            val delay = when (char) {
                '.', '!', '?' -> StreamingConfig.SENTENCE_END_DELAY_MS
                ',', ';', ':' -> StreamingConfig.CLAUSE_DELAY_MS
                ' ' -> StreamingConfig.WORD_DELAY_MS
                else -> StreamingConfig.CHARACTER_DELAY_MS
            }
            kotlinx.coroutines.delay(delay)
        }

        // Phase 4: Finalize message (remove loading state)
        _messages.value = _messages.value.map { msg ->
            if (msg.id == messageId) {
                msg.copy(
                    content = fullResponse,
                    isLoading = false,
                    thoughts = "",
                    canRetry = true
                )
            } else msg
        }

        kotlinx.coroutines.delay(StreamingConfig.MESSAGE_GAP_DELAY_MS)
    }

    fun retryMessage(message: ChatMessage) {
        if (_isProcessing.value) return

        val lastUserMessage = _messages.value.lastOrNull { it.isUser }
        val userText = lastUserMessage?.content ?: return

        // Find AI by name.
        val ai = _activeAIs.value.find { it.name == message.sender }

        if (ai != null) {
            viewModelScope.launch {
                _isProcessing.value = true
                _uiState.value = ChatUiState.Loading

                // Remove the message being retried
                _messages.value = _messages.value.filter { it.id != message.id }

                simulateSingleAIResponse(ai, userText)

                _isProcessing.value = false
                _uiState.value = ChatUiState.Idle
                _currentThought.value = ""
            }
        }
    }
    
    private fun generateAIResponse(ai: ActiveAI, userText: String): String {
        // This would normally call the actual LLM
        // For now, return placeholder responses based on personality
        return when (ai.id) {
            "nova" -> "That's a fascinating question! Let me think about it analytically... From my perspective, the key aspects to consider are the underlying patterns and what data supports different viewpoints."
            "echo" -> "Oh, that's like asking what color the wind is! 🎨 Let me paint you a picture with words... I think the answer lies somewhere between imagination and reality."
            "sage" -> "A thoughtful inquiry indeed. Throughout history, many have pondered similar questions. I would suggest considering multiple perspectives before arriving at a conclusion."
            "spark" -> "Wow, great question! ⚡ I'm so excited to explore this with you! The possibilities are endless, and I just know we'll discover something amazing!"
            "atlas" -> "Let me break this down into actionable steps. First, we should identify the core problem. Then, we can systematically work through the solution."
            "luna" -> "I sense this question comes from a place of genuine curiosity. It's okay to not have all the answers right away. Let's explore this together. 🌙"
            "cipher" -> "Logically speaking, we can approach this problem systematically. Let me analyze the variables and constraints to find the optimal solution."
            "muse" -> "What a beautiful thought! 🎨 This reminds me of how artists throughout the ages have grappled with similar themes. Let inspiration be your guide."
            "phoenix" -> "Every question is an opportunity for growth! 🔥 Even if we don't find the perfect answer, the journey of exploration transforms us."
            "zen" -> "Take a deep breath. ☯️ Sometimes the answer reveals itself when we stop searching so hard. Be present with the question."
            else -> "Thank you for sharing that thought. Let me reflect on it and provide my perspective."
        }
    }
    
    fun startPrivateChat(aiId: String) {
        val personality = BUILTIN_PERSONALITIES.find { it.name.lowercase() == aiId }
        if (personality != null) {
            _activeAIs.value = listOf(
                ActiveAI(
                    id = aiId,
                    name = personality.name,
                    avatar = personality.avatar,
                    isActive = true
                )
            )
        }
    }

    fun toggleAI(aiId: String) {
        _activeAIs.value = _activeAIs.value.map { ai ->
            if (ai.id == aiId) ai.copy(isActive = !ai.isActive)
            else ai
        }
    }
    
    fun addAI(aiId: String) {
        val personality = BUILTIN_PERSONALITIES.find { it.name.lowercase() == aiId }
        if (personality != null && _activeAIs.value.none { it.id == aiId }) {
            _activeAIs.value = _activeAIs.value + ActiveAI(
                id = aiId,
                name = personality.name,
                avatar = personality.avatar,
                isActive = true
            )
        }
    }
    
    fun removeAI(aiId: String) {
        _activeAIs.value = _activeAIs.value.filter { it.id != aiId }
    }
}
