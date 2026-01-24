/**
 * Tools Screen - View and execute AI tools
 */

package com.landseek.aichat.ui.tools

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.landseek.aichat.domain.model.toolRegistry
import com.landseek.aichat.domain.model.Tool
import com.landseek.aichat.domain.model.ToolResult
import com.landseek.aichat.ui.theme.*

@Composable
fun ToolsScreen() {
    val tools = remember { toolRegistry.listTools() }
    val toolsByCategory = remember { tools.groupBy { it.category } }
    var selectedTool by remember { mutableStateOf<Tool?>(null) }
    var toolResult by remember { mutableStateOf<ToolResult?>(null) }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(AIBackground)
    ) {
        // Header
        Text(
            text = "AI Tools",
            style = MaterialTheme.typography.headlineSmall,
            color = Color.White,
            modifier = Modifier.padding(16.dp)
        )
        
        Text(
            text = "Tools available for AI to use during conversations. You can also execute them directly.",
            style = MaterialTheme.typography.bodyMedium,
            color = AITextSecondary,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
        )
        
        HorizontalDivider(color = AIDivider)
        
        // Tools by category
        LazyColumn(
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            toolsByCategory.forEach { (category, categoryTools) ->
                item {
                    ToolCategoryHeader(category = category)
                }
                
                items(categoryTools) { tool ->
                    ToolCard(
                        tool = tool,
                        onClick = { selectedTool = tool }
                    )
                }
            }
        }
    }
    
    // Tool execution sheet
    selectedTool?.let { tool ->
        ToolExecutionSheet(
            tool = tool,
            result = toolResult,
            onDismiss = { 
                selectedTool = null
                toolResult = null
            },
            onExecute = { args ->
                toolResult = tool.execute(args)
            }
        )
    }
}

@Composable
fun ToolCategoryHeader(
    category: String,
    modifier: Modifier = Modifier
) {
    val icon = when (category.lowercase()) {
        "math" -> Icons.Default.Calculate
        "datetime" -> Icons.Default.Schedule
        "text" -> Icons.Default.TextFields
        "data" -> Icons.Default.DataObject
        "filesystem" -> Icons.Default.Folder
        "system" -> Icons.Default.Computer
        else -> Icons.Default.Build
    }
    
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = AIPrimary
        )
        Spacer(Modifier.width(8.dp))
        Text(
            text = category.uppercase(),
            style = MaterialTheme.typography.titleSmall,
            fontWeight = FontWeight.Bold,
            color = AIPrimary
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ToolCard(
    tool: Tool,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        onClick = onClick,
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = AISurface),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = tool.name,
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Medium,
                    color = Color.White
                )
                
                Spacer(Modifier.weight(1f))
                
                Icon(
                    imageVector = Icons.Default.PlayArrow,
                    contentDescription = "Execute",
                    tint = AISecondary
                )
            }
            
            Spacer(Modifier.height(4.dp))
            
            Text(
                text = tool.description.take(100) + if (tool.description.length > 100) "..." else "",
                style = MaterialTheme.typography.bodySmall,
                color = AITextSecondary
            )
            
            if (tool.parameters.isNotEmpty()) {
                Spacer(Modifier.height(8.dp))
                
                Row(
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    tool.parameters.keys.take(3).forEach { param ->
                        AssistChip(
                            onClick = { },
                            label = { Text(param, style = MaterialTheme.typography.labelSmall) },
                            modifier = Modifier.height(24.dp)
                        )
                    }
                    if (tool.parameters.size > 3) {
                        AssistChip(
                            onClick = { },
                            label = { Text("+${tool.parameters.size - 3}", style = MaterialTheme.typography.labelSmall) },
                            modifier = Modifier.height(24.dp)
                        )
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ToolExecutionSheet(
    tool: Tool,
    result: ToolResult?,
    onDismiss: () -> Unit,
    onExecute: (Map<String, Any?>) -> Unit
) {
    val paramValues = remember { mutableStateMapOf<String, String>() }
    
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        containerColor = AISurface
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            // Header
            Text(
                text = "🔧 ${tool.name}",
                style = MaterialTheme.typography.headlineSmall,
                color = Color.White
            )
            
            Spacer(Modifier.height(8.dp))
            
            Text(
                text = tool.description,
                style = MaterialTheme.typography.bodyMedium,
                color = AITextSecondary
            )
            
            Spacer(Modifier.height(16.dp))
            
            // Parameters
            if (tool.parameters.isNotEmpty()) {
                Text(
                    text = "Parameters",
                    style = MaterialTheme.typography.titleSmall,
                    color = Color.White
                )
                
                Spacer(Modifier.height(8.dp))
                
                tool.parameters.forEach { (name, param) ->
                    OutlinedTextField(
                        value = paramValues[name] ?: "",
                        onValueChange = { paramValues[name] = it },
                        label = { Text(name) },
                        placeholder = { Text(param.description, color = AITextSecondary) },
                        modifier = Modifier.fillMaxWidth(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = AIPrimary,
                            unfocusedBorderColor = AIDivider,
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White
                        ),
                        singleLine = true
                    )
                    
                    Spacer(Modifier.height(8.dp))
                }
            }
            
            Spacer(Modifier.height(16.dp))
            
            // Execute button
            Button(
                onClick = {
                    val args = paramValues.mapValues { (_, value) -> value as Any? }
                    onExecute(args)
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(Icons.Default.PlayArrow, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("Execute")
            }
            
            // Result
            result?.let { res ->
                Spacer(Modifier.height(16.dp))
                
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = if (res.success) AISecondary.copy(alpha = 0.1f) else AIError.copy(alpha = 0.1f)
                    )
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp)
                    ) {
                        Text(
                            text = if (res.success) "✅ Result" else "❌ Error",
                            style = MaterialTheme.typography.titleSmall,
                            color = if (res.success) AISecondary else AIError
                        )
                        
                        Spacer(Modifier.height(8.dp))
                        
                        Text(
                            text = res.output ?: res.error ?: "No output",
                            style = MaterialTheme.typography.bodyMedium,
                            color = Color.White
                        )
                    }
                }
            }
            
            Spacer(Modifier.height(32.dp))
        }
    }
}
