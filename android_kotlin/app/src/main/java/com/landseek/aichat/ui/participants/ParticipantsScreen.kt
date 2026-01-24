/**
 * Participants Screen - Manage AI personalities
 */

package com.landseek.aichat.ui.participants

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.landseek.aichat.domain.model.BUILTIN_PERSONALITIES
import com.landseek.aichat.domain.model.PersonalityDefinition
import com.landseek.aichat.ui.theme.*

@Composable
fun ParticipantsScreen() {
    val personalities = BUILTIN_PERSONALITIES
    var selectedPersonality by remember { mutableStateOf<PersonalityDefinition?>(null) }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(AIBackground)
    ) {
        // Header
        Text(
            text = "AI Personalities",
            style = MaterialTheme.typography.headlineSmall,
            color = Color.White,
            modifier = Modifier.padding(16.dp)
        )
        
        Text(
            text = "Manage the AI participants in your chat room. Toggle them on/off, rename, or start private conversations.",
            style = MaterialTheme.typography.bodyMedium,
            color = AITextSecondary,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
        )
        
        // Personalities list
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(personalities) { personality ->
                PersonalityCard(
                    personality = personality,
                    isActive = true, // TODO: Get from state
                    onToggle = { /* TODO */ },
                    onClick = { selectedPersonality = personality }
                )
            }
        }
    }
    
    // Detail sheet
    selectedPersonality?.let { personality ->
        PersonalityDetailSheet(
            personality = personality,
            onDismiss = { selectedPersonality = null },
            onStartPrivateChat = { /* TODO */ },
            onRename = { /* TODO */ }
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PersonalityCard(
    personality: PersonalityDefinition,
    isActive: Boolean,
    onToggle: (Boolean) -> Unit,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val accentColor = AIColors.getColorForAI(personality.name)
    
    Card(
        onClick = onClick,
        modifier = modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = AISurface),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Avatar
            Box(
                modifier = Modifier
                    .size(56.dp)
                    .clip(CircleShape)
                    .background(accentColor.copy(alpha = 0.2f)),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = personality.avatar,
                    fontSize = 28.sp
                )
            }
            
            Spacer(Modifier.width(16.dp))
            
            // Info
            Column(
                modifier = Modifier.weight(1f)
            ) {
                Text(
                    text = personality.name,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                
                Text(
                    text = personality.personality.take(50) + if (personality.personality.length > 50) "..." else "",
                    style = MaterialTheme.typography.bodySmall,
                    color = AITextSecondary
                )
                
                Spacer(Modifier.height(4.dp))
                
                Row(
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    personality.tags.take(3).forEach { tag ->
                        AssistChip(
                            onClick = { },
                            label = { Text(tag, fontSize = 10.sp) },
                            modifier = Modifier.height(24.dp)
                        )
                    }
                }
            }
            
            // Toggle
            Switch(
                checked = isActive,
                onCheckedChange = onToggle,
                colors = SwitchDefaults.colors(
                    checkedThumbColor = AIPrimary,
                    checkedTrackColor = AIPrimary.copy(alpha = 0.5f)
                )
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PersonalityDetailSheet(
    personality: PersonalityDefinition,
    onDismiss: () -> Unit,
    onStartPrivateChat: () -> Unit,
    onRename: (String) -> Unit
) {
    var showRenameDialog by remember { mutableStateOf(false) }
    
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
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = personality.avatar,
                    fontSize = 48.sp
                )
                
                Spacer(Modifier.width(16.dp))
                
                Column {
                    Text(
                        text = personality.name,
                        style = MaterialTheme.typography.headlineSmall,
                        color = Color.White
                    )
                    Text(
                        text = "Temperature: ${personality.temperature}",
                        style = MaterialTheme.typography.bodySmall,
                        color = AITextSecondary
                    )
                }
            }
            
            Spacer(Modifier.height(16.dp))
            
            // Description
            Text(
                text = personality.personality,
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White
            )
            
            Spacer(Modifier.height(16.dp))
            
            // Tags
            Row(
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                personality.tags.forEach { tag ->
                    SuggestionChip(
                        onClick = { },
                        label = { Text(tag) }
                    )
                }
            }
            
            Spacer(Modifier.height(24.dp))
            
            // Actions
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(
                    onClick = { showRenameDialog = true },
                    modifier = Modifier.weight(1f)
                ) {
                    Icon(Icons.Default.Edit, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Rename")
                }
                
                Button(
                    onClick = onStartPrivateChat,
                    modifier = Modifier.weight(1f)
                ) {
                    Icon(Icons.Default.Lock, contentDescription = null)
                    Spacer(Modifier.width(8.dp))
                    Text("Private Chat")
                }
            }
            
            Spacer(Modifier.height(32.dp))
        }
    }
    
    if (showRenameDialog) {
        RenameDialog(
            currentName = personality.name,
            onDismiss = { showRenameDialog = false },
            onConfirm = { newName ->
                onRename(newName)
                showRenameDialog = false
            }
        )
    }
}

@Composable
fun RenameDialog(
    currentName: String,
    onDismiss: () -> Unit,
    onConfirm: (String) -> Unit
) {
    var name by remember { mutableStateOf(currentName) }
    
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Rename AI") },
        text = {
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text("New name") },
                singleLine = true
            )
        },
        confirmButton = {
            TextButton(
                onClick = { onConfirm(name) }
            ) {
                Text("Rename")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}
