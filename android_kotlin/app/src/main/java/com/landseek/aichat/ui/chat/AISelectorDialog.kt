package com.landseek.aichat.ui.chat

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.landseek.aichat.domain.model.PersonalityDefinition

@Composable
fun AISelectorDialog(
    onDismiss: () -> Unit,
    availableAIs: List<PersonalityDefinition>,
    activeAIs: List<ActiveAI>,
    onAISelected: (String, Boolean) -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Select AIs") },
        text = {
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 400.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(
                    items = availableAIs,
                    key = { it.name }
                ) { ai ->
                    val aiId = ai.name.lowercase()
                    val isActive = activeAIs.any { it.id == aiId }

                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(12.dp),
                            modifier = Modifier.weight(1f)
                        ) {
                            Text(
                                text = ai.avatar,
                                style = MaterialTheme.typography.headlineSmall
                            )
                            Column {
                                Text(
                                    text = ai.name,
                                    style = MaterialTheme.typography.bodyLarge
                                )
                                Text(
                                    text = ai.tags.firstOrNull() ?: "AI Personality",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                        Switch(
                            checked = isActive,
                            onCheckedChange = { checked ->
                                onAISelected(aiId, checked)
                            }
                        )
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("Done")
            }
        }
    )
}
