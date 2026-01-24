/**
 * AI Chat App - Main composable with navigation
 */

package com.landseek.aichat.ui

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.landseek.aichat.ui.chat.ChatScreen
import com.landseek.aichat.ui.participants.ParticipantsScreen
import com.landseek.aichat.ui.settings.SettingsScreen
import com.landseek.aichat.ui.documents.DocumentsScreen
import com.landseek.aichat.ui.tools.ToolsScreen
import kotlinx.coroutines.launch

/**
 * Navigation routes
 */
sealed class Screen(val route: String, val title: String, val icon: @Composable () -> Unit) {
    data object Chat : Screen("chat", "Chat", { Icon(Icons.Default.Chat, contentDescription = "Chat") })
    data object Participants : Screen("participants", "AIs", { Icon(Icons.Default.Group, contentDescription = "Participants") })
    data object Documents : Screen("documents", "Docs", { Icon(Icons.Default.Description, contentDescription = "Documents") })
    data object Tools : Screen("tools", "Tools", { Icon(Icons.Default.Build, contentDescription = "Tools") })
    data object Settings : Screen("settings", "Settings", { Icon(Icons.Default.Settings, contentDescription = "Settings") })
}

val bottomNavItems = listOf(
    Screen.Chat,
    Screen.Participants,
    Screen.Documents,
    Screen.Tools,
    Screen.Settings
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AIChatApp() {
    val navController = rememberNavController()
    val drawerState = rememberDrawerState(initialValue = DrawerValue.Closed)
    val scope = rememberCoroutineScope()
    
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentDestination = navBackStackEntry?.destination
    val currentRoute = currentDestination?.route ?: Screen.Chat.route
    val currentScreen = bottomNavItems.find { it.route == currentRoute } ?: Screen.Chat

    ModalNavigationDrawer(
        drawerState = drawerState,
        drawerContent = {
            ModalDrawerSheet {
                Spacer(Modifier.height(16.dp))
                Text(
                    text = "🤖 AI Chat Room",
                    style = MaterialTheme.typography.headlineSmall,
                    modifier = Modifier.padding(16.dp)
                )
                HorizontalDivider()
                Spacer(Modifier.height(8.dp))
                
                bottomNavItems.forEach { screen ->
                    NavigationDrawerItem(
                        icon = { screen.icon() },
                        label = { Text(screen.title) },
                        selected = currentDestination?.hierarchy?.any { it.route == screen.route } == true,
                        onClick = {
                            scope.launch { drawerState.close() }
                            navController.navigate(screen.route) {
                                popUpTo(navController.graph.findStartDestination().id) {
                                    saveState = true
                                }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        modifier = Modifier.padding(NavigationDrawerItemDefaults.ItemPadding)
                    )
                }
            }
        }
    ) {
        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text(currentScreen.title) },
                    navigationIcon = {
                        IconButton(onClick = { scope.launch { drawerState.open() } }) {
                            Icon(Icons.Default.Menu, contentDescription = "Menu")
                        }
                    },
                    actions = {
                        if (currentRoute == Screen.Chat.route) {
                            IconButton(onClick = { /* TODO: Show AI selector */ }) {
                                Icon(Icons.Default.PersonAdd, contentDescription = "Add AI")
                            }
                        }
                    }
                )
            },
            bottomBar = {
                NavigationBar {
                    bottomNavItems.forEach { screen ->
                        NavigationBarItem(
                            icon = { screen.icon() },
                            label = { Text(screen.title) },
                            selected = currentDestination?.hierarchy?.any { it.route == screen.route } == true,
                            onClick = {
                                navController.navigate(screen.route) {
                                    popUpTo(navController.graph.findStartDestination().id) {
                                        saveState = true
                                    }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            }
                        )
                    }
                }
            }
        ) { innerPadding ->
            NavHost(
                navController = navController,
                startDestination = Screen.Chat.route,
                modifier = Modifier.padding(innerPadding)
            ) {
                composable(Screen.Chat.route) { ChatScreen() }
                composable(Screen.Participants.route) { ParticipantsScreen() }
                composable(Screen.Documents.route) { DocumentsScreen() }
                composable(Screen.Tools.route) { ToolsScreen() }
                composable(Screen.Settings.route) { SettingsScreen() }
            }
        }
    }
}
