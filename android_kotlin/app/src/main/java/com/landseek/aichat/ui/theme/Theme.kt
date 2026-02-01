/**
 * AI Chat Theme - Material 3 theme for the app
 * Enhanced with GPT Mobile patterns:
 * - ThemeMode enum for user preference
 * - DynamicTheme enum for Material You support
 * - Extended color scheme for custom colors
 */

package com.landseek.aichat.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

/**
 * Theme mode preference (from GPT Mobile pattern)
 */
enum class ThemeMode {
    SYSTEM,  // Follow system setting
    LIGHT,   // Always light
    DARK     // Always dark
}

/**
 * Dynamic theme preference (from GPT Mobile pattern)
 */
enum class DynamicTheme {
    ON,   // Use Material You colors from wallpaper
    OFF   // Use app's default colors
}

/**
 * Extended color scheme for custom app colors (from GPT Mobile)
 */
@Immutable
data class ExtendedColorScheme(
    val aiPersonalityColors: Map<String, Color> = emptyMap(),
    val messageBubbleUser: Color = UserMessageBubble,
    val messageBubbleAI: Color = AIMessageBubble,
    val messageBubblePrivate: Color = PrivateMessageBubble,
    val messageBubbleSystem: Color = SystemMessageBubble
)

// Color definitions
val Purple80 = Color(0xFFD0BCFF)
val PurpleGrey80 = Color(0xFFCCC2DC)
val Pink80 = Color(0xFFEFB8C8)

val Purple40 = Color(0xFF6650a4)
val PurpleGrey40 = Color(0xFF625b71)
val Pink40 = Color(0xFF7D5260)

// Custom AI Chat colors
val AIPrimary = Color(0xFF6200EE)
val AIPrimaryDark = Color(0xFF3700B3)
val AISecondary = Color(0xFF03DAC6)
val AIBackground = Color(0xFF121212)
val AISurface = Color(0xFF1E1E1E)
val AIError = Color(0xFFCF6679)
val AIOnPrimary = Color(0xFFFFFFFF)
val AIOnBackground = Color(0xFFFFFFFF)
val AIOnSurface = Color(0xFFFFFFFF)
val AITextSecondary = Color(0xFFB3B3B3)
val AIDivider = Color(0xFF2D2D2D)

// Message bubble colors
val AIMessageBubble = Color(0xFF2D2D3D)
val UserMessageBubble = Color(0xFF1A472A)
val PrivateMessageBubble = Color(0xFF3D2D2D)
val SystemMessageBubble = Color(0xFF2D3D2D)

private val DarkColorScheme = darkColorScheme(
    primary = AIPrimary,
    secondary = AISecondary,
    tertiary = Pink80,
    background = AIBackground,
    surface = AISurface,
    error = AIError,
    onPrimary = AIOnPrimary,
    onSecondary = Color.Black,
    onTertiary = Color.Black,
    onBackground = AIOnBackground,
    onSurface = AIOnSurface,
)

private val LightColorScheme = lightColorScheme(
    primary = Purple40,
    secondary = PurpleGrey40,
    tertiary = Pink40,
    background = Color(0xFFFFFBFE),
    surface = Color(0xFFFFFBFE),
    onPrimary = Color.White,
    onSecondary = Color.White,
    onTertiary = Color.White,
    onBackground = Color(0xFF1C1B1F),
    onSurface = Color(0xFF1C1B1F),
)

/**
 * AIChatTheme - Enhanced with GPT Mobile patterns:
 * - ThemeMode for user preference (System/Light/Dark)
 * - DynamicTheme for Material You colors
 * - Proper status bar color handling
 */
@Composable
fun AIChatTheme(
    themeMode: ThemeMode = ThemeMode.SYSTEM,
    dynamicTheme: DynamicTheme = DynamicTheme.ON,
    content: @Composable () -> Unit
) {
    // Determine if we should use dark theme based on preference
    val darkTheme = when (themeMode) {
        ThemeMode.SYSTEM -> isSystemInDarkTheme()
        ThemeMode.LIGHT -> false
        ThemeMode.DARK -> true
    }
    
    // Determine color scheme based on dynamic theme setting
    val colorScheme = when {
        dynamicTheme == DynamicTheme.ON && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }
    
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            // Use surface color for status bar (more modern look from GPT Mobile)
            window.statusBarColor = colorScheme.surface.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
