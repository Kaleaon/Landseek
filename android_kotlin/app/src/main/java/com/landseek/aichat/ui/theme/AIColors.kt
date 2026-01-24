/**
 * AI Constants - Shared constants for AI personalities
 */

package com.landseek.aichat.ui.theme

import androidx.compose.ui.graphics.Color

/**
 * Color mappings for each AI personality.
 * Used consistently across ChatScreen, ParticipantsScreen, and other UI components.
 */
object AIColors {
    val nova = Color(0xFFFFD700)
    val echo = Color(0xFFFF69B4)
    val sage = Color(0xFF4169E1)
    val spark = Color(0xFFFF4500)
    val atlas = Color(0xFF2E8B57)
    val luna = Color(0xFF9370DB)
    val cipher = Color(0xFF00CED1)
    val muse = Color(0xFFFF1493)
    val phoenix = Color(0xFFFF6347)
    val zen = Color(0xFF98FB98)
    
    /**
     * Get color for an AI by ID.
     * Returns default white color if ID not found.
     */
    fun getColorForAI(aiId: String): Color = colorMap[aiId.lowercase()] ?: Color.White
    
    /**
     * Map of AI IDs to their colors.
     */
    val colorMap: Map<String, Color> = mapOf(
        "nova" to nova,
        "echo" to echo,
        "sage" to sage,
        "spark" to spark,
        "atlas" to atlas,
        "luna" to luna,
        "cipher" to cipher,
        "muse" to muse,
        "phoenix" to phoenix,
        "zen" to zen
    )
}
