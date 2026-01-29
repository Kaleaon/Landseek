/**
 * Documents Screen - Upload and manage documents
 */

package com.landseek.aichat.ui.documents

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.landseek.aichat.data.model.DocumentEntity
import com.landseek.aichat.ui.theme.*
import kotlinx.coroutines.launch

@Composable
fun DocumentsScreen(
    viewModel: DocumentsViewModel = hiltViewModel()
) {
    val documents by viewModel.documents.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    var selectedDocument by remember { mutableStateOf<DocumentEntity?>(null) }
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    
    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri ->
        uri?.let { viewModel.uploadDocument(it) }
    }

    LaunchedEffect(Unit) {
        viewModel.snackbarMessage.collect { message ->
            snackbarHostState.showSnackbar(
                message = message,
                duration = SnackbarDuration.Short
            )
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        containerColor = AIBackground,
        modifier = Modifier.fillMaxSize()
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            Column(
                modifier = Modifier.fillMaxSize()
            ) {
                // Header
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = "Documents",
                            style = MaterialTheme.typography.headlineSmall,
                            color = Color.White
                        )
                        Text(
                            text = "${documents.size} files uploaded",
                            style = MaterialTheme.typography.bodySmall,
                            color = AITextSecondary
                        )
                    }

                    FloatingActionButton(
                        onClick = { launcher.launch(arrayOf("*/*")) },
                        containerColor = AIPrimary
                    ) {
                        Icon(Icons.Default.Add, contentDescription = "Upload")
                    }
                }

                HorizontalDivider(color = AIDivider)

                // Document list
                if (documents.isEmpty()) {
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Icon(
                                imageVector = Icons.Default.Description,
                                contentDescription = null,
                                modifier = Modifier.size(64.dp),
                                tint = AITextSecondary
                            )
                            Spacer(Modifier.height(16.dp))
                            Text(
                                text = "No documents uploaded",
                                style = MaterialTheme.typography.titleMedium,
                                color = AITextSecondary
                            )
                            Text(
                                text = "Tap + to add a document",
                                style = MaterialTheme.typography.bodySmall,
                                color = AITextSecondary
                            )
                        }
                    }
                } else {
                    LazyColumn(
                        contentPadding = PaddingValues(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        items(documents) { document ->
                            DocumentCard(
                                document = document,
                                onClick = { selectedDocument = document },
                                onQuickAnalyze = { viewModel.analyzeDocument(document) }
                            )
                        }
                    }
                }
            }

            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.align(Alignment.Center),
                    color = AIPrimary
                )
            }
        }

        // Document detail sheet
        selectedDocument?.let { document ->
            DocumentDetailSheet(
                document = document,
                onDismiss = { selectedDocument = null },
                onAnalyze = {
                    viewModel.analyzeDocument(document)
                    selectedDocument = null
                },
                onDelete = {
                    viewModel.deleteDocument(document)
                    selectedDocument = null
                }
            )
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DocumentCard(
    document: DocumentEntity,
    onClick: () -> Unit,
    onQuickAnalyze: () -> Unit,
    modifier: Modifier = Modifier
) {
    val icon = when {
        document.mimeType.startsWith("text/") -> Icons.Default.Description
        document.mimeType.contains("json") -> Icons.Default.DataObject
        document.mimeType.contains("pdf") -> Icons.Default.PictureAsPdf
        document.mimeType.startsWith("image/") -> Icons.Default.Image
        else -> Icons.Default.InsertDriveFile
    }
    
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
            // Icon
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .background(
                        color = AIPrimary.copy(alpha = 0.1f),
                        shape = RoundedCornerShape(8.dp)
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = AIPrimary
                )
            }
            
            Spacer(Modifier.width(16.dp))
            
            // Info
            Column(
                modifier = Modifier.weight(1f)
            ) {
                Text(
                    text = document.name,
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Medium,
                    color = Color.White
                )
                Text(
                    text = formatFileSize(document.sizeBytes),
                    style = MaterialTheme.typography.bodySmall,
                    color = AITextSecondary
                )
            }
            
            // Actions
            IconButton(onClick = onQuickAnalyze) {
                Icon(
                    imageVector = Icons.Default.AutoAwesome,
                    contentDescription = "Analyze",
                    tint = AISecondary
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DocumentDetailSheet(
    document: DocumentEntity,
    onDismiss: () -> Unit,
    onAnalyze: () -> Unit,
    onDelete: () -> Unit
) {
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
                Icon(
                    imageVector = Icons.Default.Description,
                    contentDescription = null,
                    modifier = Modifier.size(48.dp),
                    tint = AIPrimary
                )
                
                Spacer(Modifier.width(16.dp))
                
                Column {
                    Text(
                        text = document.name,
                        style = MaterialTheme.typography.titleLarge,
                        color = Color.White
                    )
                    Text(
                        text = formatFileSize(document.sizeBytes),
                        style = MaterialTheme.typography.bodySmall,
                        color = AITextSecondary
                    )
                }
            }
            
            Spacer(Modifier.height(24.dp))
            
            // Actions
            Button(
                onClick = onAnalyze,
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(Icons.Default.AutoAwesome, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("Analyze with AI")
            }
            
            Spacer(Modifier.height(8.dp))
            
            OutlinedButton(
                onClick = { /* TODO: View content */ },
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(Icons.Default.Visibility, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("View Content")
            }
            
            Spacer(Modifier.height(8.dp))
            
            OutlinedButton(
                onClick = onDelete,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = AIError)
            ) {
                Icon(Icons.Default.Delete, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text("Delete")
            }
            
            Spacer(Modifier.height(32.dp))
        }
    }
}

private fun formatFileSize(bytes: Long): String {
    return when {
        bytes < 1024 -> "$bytes B"
        bytes < 1024 * 1024 -> "${"%.1f".format(bytes / 1024.0)} KB"
        else -> "${"%.2f".format(bytes / (1024.0 * 1024))} MB"
    }
}
