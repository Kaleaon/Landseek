/**
 * Chat Screen - Main chat interface
 * Enhanced with GPT Mobile design patterns:
 * - Markdown rendering in chat bubbles
 * - Loading cursor animation
 * - Long-press actions (copy, select, retry)
 * - Animated content size
 * - ThinkingBlock for RAG/RLM status
 */

package com.landseek.aichat.ui.chat

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import androidx.compose.animation.animateContentSize
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.halilibo.richtext.commonmark.CommonmarkAstNodeParser
import com.halilibo.richtext.markdown.BasicMarkdown
import com.halilibo.richtext.ui.material3.RichText
import com.landseek.aichat.ui.theme.*
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.*

/**
 * Chat message data class for UI
 * Enhanced with streaming support and thinking status
 */
data class ChatMessage(
    val id: String = UUID.randomUUID().toString(),
    val sender: String,
    val avatar: String,
    val content: String,
    val timestamp: Long = System.currentTimeMillis(),
    val isUser: Boolean = false,
    val isPrivate: Boolean = false,
    val senderColor: Color = Color.White,
    val isLoading: Boolean = false,  // Show loading cursor
    val thoughts: String = "",        // Thinking/RAG status
    val canRetry: Boolean = false     // Allow retry action
)

/**
 * Active AI data class
 */
data class ActiveAI(
    val id: String,
    val name: String,
    val avatar: String,
    val isActive: Boolean = true
)

@Composable
fun ChatScreen(
    viewModel: ChatViewModel
) {
    val messages by viewModel.messages.collectAsState()
    val activeAIs by viewModel.activeAIs.collectAsState()
    val inputText by viewModel.inputText.collectAsState()
    val isProcessing by viewModel.isProcessing.collectAsState()
    val uiState by viewModel.uiState.collectAsState()
    val currentThought by viewModel.currentThought.collectAsState()
    
    val listState = rememberLazyListState()
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    
    // Snackbar for actions
    val snackbarHostState = remember { SnackbarHostState() }
    
    // Scroll to bottom when new message arrives
    LaunchedEffect(messages.size) {
        if (messages.isNotEmpty()) {
            listState.animateScrollToItem(messages.size - 1)
        }
    }
    
    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        containerColor = AIBackground
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            // Active AIs bar
            ActiveAIsBar(
                activeAIs = activeAIs,
                onAIClick = { viewModel.toggleAI(it) }
            )
            
            HorizontalDivider(color = AIDivider)
            
            // Messages list
            LazyColumn(
                state = listState,
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .padding(horizontal = 8.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp),
                contentPadding = PaddingValues(vertical = 8.dp)
            ) {
                items(messages, key = { it.id }) { message ->
                    ChatBubble(
                        message = message,
                        onCopyClick = {
                            copyToClipboard(context, message.content)
                            scope.launch {
                                snackbarHostState.showSnackbar("Copied to clipboard")
                            }
                        },
                        onRetryClick = {
                            // TODO: Implement retry logic
                        }
                    )
                }
            }
            
            // ThinkingBlock when AI is processing (from GPT Mobile pattern)
            if (isProcessing && currentThought.isNotEmpty()) {
                ThinkingBlock(
                    thoughts = currentThought,
                    isLoading = true,
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                )
            }
            
            // Input area
            ChatInput(
                text = inputText,
                onTextChange = viewModel::onInputTextChange,
                onSend = viewModel::sendMessage,
                isProcessing = isProcessing,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

@Composable
fun ActiveAIsBar(
    activeAIs: List<ActiveAI>,
    onAIClick: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(8.dp)
            .horizontalScroll(rememberScrollState()),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        activeAIs.forEach { ai ->
            AIChip(
                ai = ai,
                onClick = { onAIClick(ai.id) }
            )
        }
    }
}

@Composable
private fun rememberScrollState() = androidx.compose.foundation.rememberScrollState()

@Composable
fun AIChip(
    ai: ActiveAI,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        onClick = onClick,
        modifier = modifier,
        shape = RoundedCornerShape(16.dp),
        color = if (ai.isActive) AIPrimary.copy(alpha = 0.3f) else AISurface
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            Text(
                text = ai.avatar,
                fontSize = 14.sp
            )
            Text(
                text = ai.name,
                style = MaterialTheme.typography.bodySmall,
                color = if (ai.isActive) Color.White else AITextSecondary
            )
        }
    }
}

/**
 * ChatBubble - Enhanced with GPT Mobile patterns:
 * - Markdown rendering using richtext-commonmark
 * - Loading cursor (●) with animateContentSize
 * - Long-press gestures for copy/select/retry
 * - ThinkingBlock for RAG/RLM status
 */
@Composable
fun ChatBubble(
    message: ChatMessage,
    onCopyClick: () -> Unit = {},
    onRetryClick: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    var showActions by remember { mutableStateOf(false) }
    
    val bubbleColor = when {
        message.isUser -> UserMessageBubble
        message.isPrivate -> PrivateMessageBubble
        else -> AIMessageBubble
    }
    
    val alignment = if (message.isUser) Alignment.End else Alignment.Start
    val shape = if (message.isUser) {
        RoundedCornerShape(16.dp, 16.dp, 4.dp, 16.dp)
    } else {
        RoundedCornerShape(16.dp, 16.dp, 16.dp, 4.dp)
    }
    
    // Parse markdown content (memoized for performance)
    val parser = remember { CommonmarkAstNodeParser() }
    val displayText = if (message.isLoading) {
        message.content + "●"  // Loading cursor from GPT Mobile
    } else {
        message.content
    }
    val astNode = remember(displayText) { parser.parse(displayText.trimIndent()) }
    
    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp),
        horizontalAlignment = alignment
    ) {
        // ThinkingBlock for AI messages with thoughts (RAG/RLM status)
        if (message.thoughts.isNotBlank() && !message.isUser) {
            ThinkingBlock(
                thoughts = message.thoughts,
                isLoading = message.isLoading,
                aiAvatar = message.avatar,
                modifier = Modifier
                    .widthIn(max = 300.dp)
                    .padding(bottom = 4.dp)
            )
        }
        
        Surface(
            modifier = Modifier
                .widthIn(max = 300.dp)
                .clip(shape)
                .pointerInput(Unit) {
                    detectTapGestures(
                        onLongPress = { showActions = true }
                    )
                }
                .animateContentSize(),  // Smooth expansion from GPT Mobile
            color = bubbleColor,
            shape = shape
        ) {
            Column(
                modifier = Modifier.padding(12.dp)
            ) {
                // Header
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(
                        text = "${message.avatar} ${message.sender}",
                        style = MaterialTheme.typography.bodySmall,
                        fontWeight = FontWeight.Bold,
                        color = message.senderColor
                    )
                    Text(
                        text = formatTimestamp(message.timestamp),
                        style = MaterialTheme.typography.labelSmall,
                        color = AITextSecondary
                    )
                    if (message.isPrivate) {
                        Icon(
                            imageVector = Icons.Default.Lock,
                            contentDescription = "Private",
                            modifier = Modifier.size(12.dp),
                            tint = AITextSecondary
                        )
                    }
                }
                
                Spacer(Modifier.height(4.dp))
                
                // Content with Markdown rendering (from GPT Mobile)
                RichText(
                    modifier = Modifier.animateContentSize()
                ) {
                    BasicMarkdown(astNode = astNode)
                }
            }
        }
        
        // Action buttons (from GPT Mobile long-press pattern)
        if (showActions && !message.isLoading) {
            MessageActions(
                canRetry = message.canRetry && !message.isUser,
                onCopyClick = {
                    onCopyClick()
                    showActions = false
                },
                onRetryClick = {
                    onRetryClick()
                    showActions = false
                },
                onDismiss = { showActions = false }
            )
        }
    }
}

/**
 * Message action buttons (from GPT Mobile)
 */
@Composable
private fun MessageActions(
    canRetry: Boolean,
    onCopyClick: () -> Unit,
    onRetryClick: () -> Unit,
    onDismiss: () -> Unit
) {
    Row(
        modifier = Modifier.padding(start = 8.dp, top = 4.dp),
        horizontalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        // Copy button
        IconButton(
            onClick = onCopyClick,
            modifier = Modifier.size(32.dp)
        ) {
            Icon(
                imageVector = Icons.Default.ContentCopy,
                contentDescription = "Copy",
                tint = AITextSecondary,
                modifier = Modifier.size(16.dp)
            )
        }
        
        // Retry button (only for AI messages that can be retried)
        if (canRetry) {
            IconButton(
                onClick = onRetryClick,
                modifier = Modifier.size(32.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.Refresh,
                    contentDescription = "Retry",
                    tint = AITextSecondary,
                    modifier = Modifier.size(16.dp)
                )
            }
        }
        
        // Dismiss button
        IconButton(
            onClick = onDismiss,
            modifier = Modifier.size(32.dp)
        ) {
            Icon(
                imageVector = Icons.Default.Close,
                contentDescription = "Close",
                tint = AITextSecondary,
                modifier = Modifier.size(16.dp)
            )
        }
    }
}

/**
 * Copy text to clipboard helper
 */
private fun copyToClipboard(context: Context, text: String) {
    val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
    val clip = ClipData.newPlainText("Chat Message", text)
    clipboard.setPrimaryClip(clip)
}

@Composable
fun ChatInput(
    text: String,
    onTextChange: (String) -> Unit,
    onSend: () -> Unit,
    isProcessing: Boolean,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        color = AISurface,
        tonalElevation = 2.dp
    ) {
        Row(
            modifier = Modifier
                .padding(8.dp)
                .fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Attachment button
            IconButton(
                onClick = { /* TODO: Attach file */ }
            ) {
                Icon(
                    imageVector = Icons.Default.AttachFile,
                    contentDescription = "Attach",
                    tint = AITextSecondary
                )
            }
            
            // Text field
            OutlinedTextField(
                value = text,
                onValueChange = onTextChange,
                modifier = Modifier.weight(1f),
                placeholder = { Text("Type a message...", color = AITextSecondary) },
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = AIPrimary,
                    unfocusedBorderColor = AIDivider,
                    focusedTextColor = Color.White,
                    unfocusedTextColor = Color.White
                ),
                singleLine = false,
                maxLines = 4
            )
            
            // Send button
            IconButton(
                onClick = onSend,
                enabled = text.isNotBlank() && !isProcessing
            ) {
                if (isProcessing) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(24.dp),
                        color = AIPrimary
                    )
                } else {
                    Icon(
                        imageVector = Icons.Default.Send,
                        contentDescription = "Send",
                        tint = if (text.isNotBlank()) AIPrimary else AITextSecondary
                    )
                }
            }
        }
    }
}

private fun formatTimestamp(timestamp: Long): String {
    val sdf = SimpleDateFormat("HH:mm", Locale.getDefault())
    return sdf.format(Date(timestamp))
}
