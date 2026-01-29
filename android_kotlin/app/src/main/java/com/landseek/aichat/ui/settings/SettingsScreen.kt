/**
 * Settings Screen - App configuration
 */

package com.landseek.aichat.ui.settings

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.unit.dp
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.ui.platform.LocalContext
import androidx.hilt.navigation.compose.hiltViewModel
import android.widget.Toast
import com.landseek.aichat.domain.model.*
import com.landseek.aichat.ui.theme.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable
fun SettingsScreen(
    viewModel: SettingsViewModel = hiltViewModel()
) {
    var userName by remember { mutableStateOf("User") }
    var selectedModel by remember { mutableStateOf("gemma3-4b-gguf") }
    var ollamaUrl by remember { mutableStateOf("http://localhost:11434") }
    var darkMode by remember { mutableStateOf(true) }
    var notificationsEnabled by remember { mutableStateOf(true) }
    
    // P2P State
    var showHostDialog by remember { mutableStateOf(false) }
    var showJoinDialog by remember { mutableStateOf(false) }
    var shareCode by remember { mutableStateOf("") }
    var joinCode by remember { mutableStateOf("") }
    var p2pStatus by remember { mutableStateOf<String?>(null) }
    
    val p2pManager = remember { getP2PNetworkManager() }
    val connectionState by p2pManager.connectionState.collectAsState()
    val scope = rememberCoroutineScope()

    val context = LocalContext.current
    val uiState by viewModel.uiState.collectAsState()

    // Handle UI State feedback
    LaunchedEffect(uiState) {
        when (val state = uiState) {
            is SettingsUiState.Success -> {
                Toast.makeText(context, state.message, Toast.LENGTH_SHORT).show()
                viewModel.resetUiState()
            }
            is SettingsUiState.Error -> {
                Toast.makeText(context, state.message, Toast.LENGTH_LONG).show()
                viewModel.resetUiState()
            }
            else -> {}
        }
    }

    val exportLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.CreateDocument("application/json")
    ) { uri ->
        uri?.let {
            scope.launch {
                try {
                    val json = viewModel.getExportDataJson()
                    withContext(Dispatchers.IO) {
                        context.contentResolver.openOutputStream(it)?.use { output ->
                            output.write(json.toByteArray())
                        }
                    }
                    Toast.makeText(context, "Data exported successfully", Toast.LENGTH_SHORT).show()
                } catch (e: Exception) {
                    Toast.makeText(context, "Export failed: ${e.message}", Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    val importLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri ->
        uri?.let {
            scope.launch {
                try {
                    val json = withContext(Dispatchers.IO) {
                        context.contentResolver.openInputStream(it)?.bufferedReader().use { reader ->
                            reader?.readText()
                        }
                    }
                    json?.let { viewModel.importData(it) }
                } catch (e: Exception) {
                    Toast.makeText(context, "Read failed: ${e.message}", Toast.LENGTH_LONG).show()
                }
            }
        }
    }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(AIBackground)
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        // User Profile Section
        SettingsSection(title = "Profile") {
            SettingsTextField(
                label = "Your Name",
                value = userName,
                onValueChange = { userName = it },
                icon = Icons.Default.Person
            )
        }
        
        Spacer(Modifier.height(16.dp))
        
        // Model Settings
        SettingsSection(title = "AI Model") {
            SettingsDropdown(
                label = "Model",
                options = MODEL_CATALOG.values.map { it.name to it.id },
                selectedOption = selectedModel,
                onOptionSelected = { selectedModel = it },
                icon = Icons.Default.Memory
            )
            
            Spacer(Modifier.height(8.dp))
            
            SettingsTextField(
                label = "Ollama URL",
                value = ollamaUrl,
                onValueChange = { ollamaUrl = it },
                icon = Icons.Default.Link
            )
            
            Spacer(Modifier.height(8.dp))
            
            // Model info
            MODEL_CATALOG[selectedModel]?.let { model ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = AIPrimary.copy(alpha = 0.1f))
                ) {
                    Column(
                        modifier = Modifier.padding(12.dp)
                    ) {
                        Text(
                            text = model.name,
                            style = MaterialTheme.typography.titleSmall,
                            color = Color.White
                        )
                        Text(
                            text = model.description,
                            style = MaterialTheme.typography.bodySmall,
                            color = AITextSecondary
                        )
                        Spacer(Modifier.height(4.dp))
                        Row(
                            horizontalArrangement = Arrangement.spacedBy(16.dp)
                        ) {
                            Text(
                                text = "📦 ${model.sizeHuman}",
                                style = MaterialTheme.typography.labelSmall,
                                color = AITextSecondary
                            )
                            Text(
                                text = "💾 ${model.requiredRamMb}MB RAM",
                                style = MaterialTheme.typography.labelSmall,
                                color = AITextSecondary
                            )
                            if (model.supportsTpu) {
                                Text(
                                    text = "⚡ TPU",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = AISecondary
                                )
                            }
                        }
                    }
                }
            }
        }
        
        Spacer(Modifier.height(16.dp))
        
        // Appearance
        SettingsSection(title = "Appearance") {
            SettingsSwitch(
                label = "Dark Mode",
                description = "Use dark theme",
                checked = darkMode,
                onCheckedChange = { darkMode = it },
                icon = Icons.Default.DarkMode
            )
        }
        
        Spacer(Modifier.height(16.dp))
        
        // Notifications
        SettingsSection(title = "Notifications") {
            SettingsSwitch(
                label = "Enable Notifications",
                description = "Receive notifications for new messages",
                checked = notificationsEnabled,
                onCheckedChange = { notificationsEnabled = it },
                icon = Icons.Default.Notifications
            )
        }
        
        Spacer(Modifier.height(16.dp))
        
        // P2P Settings
        SettingsSection(title = "P2P Networking") {
            // Connection Status
            when (val state = connectionState) {
                is P2PConnectionState.Connected -> {
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = Color(0xFF2E7D32).copy(alpha = 0.2f)
                        ),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(
                            modifier = Modifier.padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                Icons.Default.Wifi,
                                contentDescription = null,
                                tint = Color(0xFF4CAF50)
                            )
                            Spacer(Modifier.width(8.dp))
                            Column {
                                Text("Connected", color = Color(0xFF4CAF50))
                                Text(
                                    "Room: ${state.roomInfo.roomCode}",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = AITextSecondary
                                )
                            }
                            Spacer(Modifier.weight(1f))
                            TextButton(onClick = { p2pManager.disconnect() }) {
                                Text("Disconnect", color = Color(0xFFFF5252))
                            }
                        }
                    }
                    Spacer(Modifier.height(8.dp))
                }
                is P2PConnectionState.Connecting -> {
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(20.dp),
                            strokeWidth = 2.dp
                        )
                        Spacer(Modifier.width(8.dp))
                        Text("Connecting...", color = AITextSecondary)
                    }
                    Spacer(Modifier.height(8.dp))
                }
                is P2PConnectionState.Error -> {
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = Color(0xFFD32F2F).copy(alpha = 0.2f)
                        ),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(
                            modifier = Modifier.padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                Icons.Default.Error,
                                contentDescription = null,
                                tint = Color(0xFFFF5252)
                            )
                            Spacer(Modifier.width(8.dp))
                            Text(
                                "Error: ${state.message}",
                                color = Color(0xFFFF5252),
                                style = MaterialTheme.typography.bodySmall
                            )
                        }
                    }
                    Spacer(Modifier.height(8.dp))
                }
                else -> {}
            }
            
            SettingsButton(
                label = "Host Room",
                description = "Share your AI with others over the network",
                icon = Icons.Default.Share,
                onClick = { 
                    val roomInfo = p2pManager.hostRoom(name = "AI Chat Room")
                    shareCode = roomInfo.shareCodeLocal
                    showHostDialog = true
                }
            )
            
            Spacer(Modifier.height(8.dp))
            
            SettingsButton(
                label = "Join Room",
                description = "Connect to someone else's AI",
                icon = Icons.Default.PersonAdd,
                onClick = { showJoinDialog = true }
            )
        }
        
        Spacer(Modifier.height(16.dp))
        
        // Data Management
        SettingsSection(title = "Data") {
            SettingsButton(
                label = "Export Data",
                description = "Save chat history and settings",
                icon = Icons.Default.Download,
                onClick = {
                    val timestamp = java.text.SimpleDateFormat("yyyyMMdd_HHmmss", java.util.Locale.getDefault()).format(java.util.Date())
                    exportLauncher.launch("aichat_backup_$timestamp.json")
                }
            )
            
            Spacer(Modifier.height(8.dp))
            
            SettingsButton(
                label = "Import Data",
                description = "Restore from backup",
                icon = Icons.Default.Upload,
                onClick = {
                    importLauncher.launch(arrayOf("application/json"))
                }
            )
            
            Spacer(Modifier.height(8.dp))
            
            SettingsButton(
                label = "Clear History",
                description = "Delete all chat messages",
                icon = Icons.Default.Delete,
                onClick = { viewModel.clearHistory() },
                isDestructive = true
            )
        }
        
        Spacer(Modifier.height(16.dp))
        
        // About
        SettingsSection(title = "About") {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = AISurface)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text(
                        text = "🤖 AI Chat Room",
                        style = MaterialTheme.typography.titleMedium,
                        color = Color.White
                    )
                    Text(
                        text = "Version 1.0.0",
                        style = MaterialTheme.typography.bodySmall,
                        color = AITextSecondary
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(
                        text = "Powered by Gemma 3 4B, optimized for Pixel 10 Pro TPU.",
                        style = MaterialTheme.typography.bodySmall,
                        color = AITextSecondary
                    )
                }
            }
        }
        
        Spacer(Modifier.height(32.dp))
    }
    
    // Host Room Dialog
    if (showHostDialog) {
        val clipboardManager = LocalClipboardManager.current
        AlertDialog(
            onDismissRequest = { showHostDialog = false },
            title = { Text("Room Hosted", color = Color.White) },
            text = {
                Column {
                    Text(
                        "Share this code with others to let them join:",
                        color = AITextSecondary
                    )
                    Spacer(Modifier.height(16.dp))
                    Card(
                        colors = CardDefaults.cardColors(containerColor = AISurface),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                shareCode,
                                style = MaterialTheme.typography.titleMedium,
                                color = AIPrimary
                            )
                            IconButton(onClick = {
                                clipboardManager.setText(AnnotatedString(shareCode))
                            }) {
                                Icon(
                                    Icons.Default.ContentCopy,
                                    contentDescription = "Copy",
                                    tint = AITextSecondary
                                )
                            }
                        }
                    }
                    Spacer(Modifier.height(8.dp))
                    Text(
                        "Others can use 'Join Room' and paste this code to connect.",
                        style = MaterialTheme.typography.bodySmall,
                        color = AITextSecondary
                    )
                }
            },
            confirmButton = {
                TextButton(onClick = { showHostDialog = false }) {
                    Text("Done", color = AIPrimary)
                }
            },
            containerColor = AIBackground
        )
    }
    
    // Join Room Dialog
    if (showJoinDialog) {
        AlertDialog(
            onDismissRequest = { showJoinDialog = false },
            title = { Text("Join Room", color = Color.White) },
            text = {
                Column {
                    Text(
                        "Enter the share code from the room host:",
                        color = AITextSecondary
                    )
                    Spacer(Modifier.height(16.dp))
                    OutlinedTextField(
                        value = joinCode,
                        onValueChange = { joinCode = it },
                        label = { Text("Share Code") },
                        modifier = Modifier.fillMaxWidth(),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = AIPrimary,
                            unfocusedBorderColor = AIDivider,
                            focusedTextColor = Color.White,
                            unfocusedTextColor = Color.White,
                            focusedLabelColor = AIPrimary,
                            unfocusedLabelColor = AITextSecondary
                        ),
                        singleLine = true
                    )
                    if (p2pStatus != null) {
                        Spacer(Modifier.height(8.dp))
                        Text(
                            p2pStatus!!,
                            color = if (p2pStatus!!.contains("Error")) AIError else Color(0xFF4CAF50),
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        scope.launch {
                            p2pStatus = "Connecting..."
                            val result = p2pManager.joinRoom(joinCode, userName)
                            result.fold(
                                onSuccess = {
                                    p2pStatus = "Connected!"
                                    showJoinDialog = false
                                    joinCode = ""
                                },
                                onFailure = {
                                    p2pStatus = "Error: ${it.message}"
                                }
                            )
                        }
                    }
                ) {
                    Text("Connect", color = AIPrimary)
                }
            },
            dismissButton = {
                TextButton(onClick = { 
                    showJoinDialog = false
                    joinCode = ""
                    p2pStatus = null
                }) {
                    Text("Cancel", color = AITextSecondary)
                }
            },
            containerColor = AIBackground
        )
    }
}

@Composable
fun SettingsSection(
    title: String,
    content: @Composable ColumnScope.() -> Unit
) {
    Column {
        Text(
            text = title,
            style = MaterialTheme.typography.titleSmall,
            color = AIPrimary,
            modifier = Modifier.padding(bottom = 8.dp)
        )
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = AISurface),
            shape = RoundedCornerShape(12.dp)
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                content = content
            )
        }
    }
}

@Composable
fun SettingsTextField(
    label: String,
    value: String,
    onValueChange: (String) -> Unit,
    icon: ImageVector,
    modifier: Modifier = Modifier
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label) },
        leadingIcon = { Icon(icon, contentDescription = null, tint = AITextSecondary) },
        modifier = modifier.fillMaxWidth(),
        colors = OutlinedTextFieldDefaults.colors(
            focusedBorderColor = AIPrimary,
            unfocusedBorderColor = AIDivider,
            focusedTextColor = Color.White,
            unfocusedTextColor = Color.White,
            focusedLabelColor = AIPrimary,
            unfocusedLabelColor = AITextSecondary
        ),
        singleLine = true
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsDropdown(
    label: String,
    options: List<Pair<String, String>>,
    selectedOption: String,
    onOptionSelected: (String) -> Unit,
    icon: ImageVector,
    modifier: Modifier = Modifier
) {
    var expanded by remember { mutableStateOf(false) }
    val selectedDisplay = options.find { it.second == selectedOption }?.first ?: ""
    
    ExposedDropdownMenuBox(
        expanded = expanded,
        onExpandedChange = { expanded = !expanded },
        modifier = modifier.fillMaxWidth()
    ) {
        OutlinedTextField(
            value = selectedDisplay,
            onValueChange = { },
            readOnly = true,
            label = { Text(label) },
            leadingIcon = { Icon(icon, contentDescription = null, tint = AITextSecondary) },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
            modifier = Modifier
                .fillMaxWidth()
                .menuAnchor(),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = AIPrimary,
                unfocusedBorderColor = AIDivider,
                focusedTextColor = Color.White,
                unfocusedTextColor = Color.White,
                focusedLabelColor = AIPrimary,
                unfocusedLabelColor = AITextSecondary
            )
        )
        
        ExposedDropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false }
        ) {
            options.forEach { (display, value) ->
                DropdownMenuItem(
                    text = { Text(display) },
                    onClick = {
                        onOptionSelected(value)
                        expanded = false
                    }
                )
            }
        }
    }
}

@Composable
fun SettingsSwitch(
    label: String,
    description: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
    icon: ImageVector,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = AITextSecondary
        )
        
        Spacer(Modifier.width(16.dp))
        
        Column(
            modifier = Modifier.weight(1f)
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White
            )
            Text(
                text = description,
                style = MaterialTheme.typography.bodySmall,
                color = AITextSecondary
            )
        }
        
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
            colors = SwitchDefaults.colors(
                checkedThumbColor = AIPrimary,
                checkedTrackColor = AIPrimary.copy(alpha = 0.5f)
            )
        )
    }
}

@Composable
fun SettingsButton(
    label: String,
    description: String,
    icon: ImageVector,
    onClick: () -> Unit,
    isDestructive: Boolean = false,
    modifier: Modifier = Modifier
) {
    val contentColor = if (isDestructive) AIError else Color.White
    
    Surface(
        onClick = onClick,
        modifier = modifier.fillMaxWidth(),
        color = Color.Transparent
    ) {
        Row(
            modifier = Modifier.padding(vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = if (isDestructive) AIError else AITextSecondary
            )
            
            Spacer(Modifier.width(16.dp))
            
            Column(
                modifier = Modifier.weight(1f)
            ) {
                Text(
                    text = label,
                    style = MaterialTheme.typography.bodyMedium,
                    color = contentColor
                )
                Text(
                    text = description,
                    style = MaterialTheme.typography.bodySmall,
                    color = if (isDestructive) AIError.copy(alpha = 0.7f) else AITextSecondary
                )
            }
            
            Icon(
                imageVector = Icons.Default.ChevronRight,
                contentDescription = null,
                tint = AITextSecondary
            )
        }
    }
}
