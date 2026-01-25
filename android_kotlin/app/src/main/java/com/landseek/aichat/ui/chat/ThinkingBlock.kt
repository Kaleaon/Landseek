/**
 * Thinking Block Component - Shows AI reasoning/RAG status
 * Inspired by GPT Mobile's ThinkingBlock for chain-of-thought models
 */

package com.landseek.aichat.ui.chat

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ExpandLess
import androidx.compose.material.icons.filled.ExpandMore
import androidx.compose.material.icons.filled.Psychology
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.unit.dp
import com.landseek.aichat.ui.theme.*

/**
 * ThinkingBlock displays the AI's reasoning process, RAG retrieval status,
 * or RLM context processing. Collapsed by default, expandable on click.
 *
 * @param thoughts The current thought or reasoning text
 * @param isLoading Whether the AI is still thinking
 * @param aiAvatar The avatar emoji of the thinking AI
 * @param modifier Modifier for the component
 */
@Composable
fun ThinkingBlock(
    thoughts: String,
    isLoading: Boolean,
    aiAvatar: String = "🧠",
    modifier: Modifier = Modifier
) {
    var isExpanded by remember { mutableStateOf(false) }
    
    // Animated thinking indicator
    val infiniteTransition = rememberInfiniteTransition(label = "thinking")
    val alpha by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(800),
            repeatMode = RepeatMode.Reverse
        ),
        label = "alpha"
    )
    
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .clickable { isExpanded = !isExpanded },
        color = AISurface.copy(alpha = 0.7f),
        shape = RoundedCornerShape(8.dp)
    ) {
        Column(
            modifier = Modifier.padding(12.dp)
        ) {
            // Header row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // Thinking icon with pulse animation when loading
                    Icon(
                        imageVector = Icons.Default.Psychology,
                        contentDescription = "Thinking",
                        tint = if (isLoading) AIPrimary.copy(alpha = alpha) else AITextSecondary,
                        modifier = Modifier.size(20.dp)
                    )
                    
                    Text(
                        text = if (isLoading) "Thinking..." else "Thought Process",
                        style = MaterialTheme.typography.labelMedium,
                        color = AITextSecondary,
                        fontStyle = FontStyle.Italic
                    )
                    
                    // Animated dots when loading
                    if (isLoading) {
                        ThinkingDots()
                    }
                }
                
                // Expand/collapse icon
                Icon(
                    imageVector = if (isExpanded) Icons.Default.ExpandLess else Icons.Default.ExpandMore,
                    contentDescription = if (isExpanded) "Collapse" else "Expand",
                    tint = AITextSecondary,
                    modifier = Modifier.size(20.dp)
                )
            }
            
            // Expandable content
            AnimatedVisibility(
                visible = isExpanded,
                enter = expandVertically() + fadeIn(),
                exit = shrinkVertically() + fadeOut()
            ) {
                Column(
                    modifier = Modifier.padding(top = 8.dp)
                ) {
                    HorizontalDivider(
                        color = AIDivider,
                        modifier = Modifier.padding(vertical = 4.dp)
                    )
                    
                    Text(
                        text = thoughts.ifEmpty { "Processing context and retrieving relevant information..." },
                        style = MaterialTheme.typography.bodySmall,
                        color = AITextSecondary.copy(alpha = 0.8f),
                        modifier = Modifier.padding(top = 4.dp)
                    )
                }
            }
        }
    }
}

/**
 * Animated thinking dots (...)
 */
@Composable
private fun ThinkingDots() {
    val infiniteTransition = rememberInfiniteTransition(label = "dots")
    
    Row(horizontalArrangement = Arrangement.spacedBy(2.dp)) {
        repeat(3) { index ->
            val delay = index * 200
            val alpha by infiniteTransition.animateFloat(
                initialValue = 0.3f,
                targetValue = 1f,
                animationSpec = infiniteRepeatable(
                    animation = tween(600, delayMillis = delay),
                    repeatMode = RepeatMode.Reverse
                ),
                label = "dot$index"
            )
            
            Text(
                text = "•",
                style = MaterialTheme.typography.labelMedium,
                color = AIPrimary.copy(alpha = alpha)
            )
        }
    }
}

/**
 * RAG Status indicator - shows retrieval progress
 */
@Composable
fun RAGStatusIndicator(
    status: String,
    progress: Float = -1f,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 12.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Icon(
            imageVector = Icons.Default.Psychology,
            contentDescription = "RAG",
            tint = AISecondary,
            modifier = Modifier.size(16.dp)
        )
        
        Text(
            text = status,
            style = MaterialTheme.typography.labelSmall,
            color = AITextSecondary
        )
        
        if (progress >= 0f) {
            LinearProgressIndicator(
                progress = { progress },
                modifier = Modifier
                    .weight(1f)
                    .height(4.dp),
                color = AISecondary,
                trackColor = AIDivider
            )
        }
    }
}
