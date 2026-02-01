/**
 * AI State Management - Persistent State for AI Personalities
 *
 * This module manages persistent state for AI personalities including:
 * - Chat history (per AI)
 * - Emotions and mood
 * - Customizable names
 * - Personality traits
 * - Private conversations between participants
 *
 * All data is stored in the public Documents folder for accessibility.
 * 
 * Converted from Python: src/ai_state.py
 */

package com.landseek.aichat.domain.model

import kotlinx.serialization.Serializable
import java.time.Instant

/**
 * Emotional states for AI personalities.
 */
enum class EmotionalState(val value: String) {
    NEUTRAL("neutral"),
    HAPPY("happy"),
    CURIOUS("curious"),
    THOUGHTFUL("thoughtful"),
    EXCITED("excited"),
    CALM("calm"),
    FOCUSED("focused"),
    PLAYFUL("playful"),
    EMPATHETIC("empathetic"),
    INSPIRED("inspired")
}

/**
 * A single entry in chat history.
 */
@Serializable
data class ChatHistoryEntry(
    val timestamp: String,
    val sender: String,
    val content: String,
    val isPrivate: Boolean = false,
    val privateWith: String? = null  // Who the private chat was with
)

/**
 * A private conversation between two participants.
 */
@Serializable
data class PrivateConversation(
    val participantA: String,  // First participant (can be AI or user)
    val participantB: String,  // Second participant (can be AI or user)
    val messages: MutableList<ChatHistoryEntry> = mutableListOf(),
    val createdAt: String = Instant.now().toString(),
    var lastActivity: String = Instant.now().toString()
) {
    /**
     * Generate a unique conversation ID.
     */
    val conversationId: String
        get() {
            // Sort names to ensure consistent ID regardless of order
            val names = listOf(participantA, participantB).sorted()
            return "${names[0]}__${names[1]}"
        }

    /**
     * Add a message to the conversation.
     */
    fun addMessage(sender: String, content: String) {
        val entry = ChatHistoryEntry(
            timestamp = Instant.now().toString(),
            sender = sender,
            content = content,
            isPrivate = true,
            privateWith = if (sender == participantA) participantB else participantA
        )
        messages.add(entry)
        lastActivity = Instant.now().toString()
    }

    /**
     * Get recent messages.
     */
    fun getRecentMessages(count: Int = 10): List<ChatHistoryEntry> =
        messages.takeLast(count)
}

/**
 * Mood history entry.
 */
@Serializable
data class MoodHistoryEntry(
    val emotion: String,
    val intensity: Float,
    val timestamp: String
)

/**
 * Relationship data with another participant.
 */
@Serializable
data class RelationshipData(
    var sentiment: String = "neutral",
    var interactionCount: Int = 0,
    val notes: MutableList<RelationshipNote> = mutableListOf(),
    val firstMet: String = Instant.now().toString(),
    var lastInteraction: String? = null
)

/**
 * A note about a relationship.
 */
@Serializable
data class RelationshipNote(
    val note: String,
    val timestamp: String
)

/**
 * Persistent state for an AI personality.
 */
@Serializable
data class AIState(
    // Identity
    val aiId: String,  // Unique identifier (e.g., "nova", "echo")
    var displayName: String,  // Customizable display name
    val originalName: String,  // Original built-in name

    // Personality
    val personality: String,  // Description of behavior
    val avatar: String = "🤖",
    val tags: List<String> = emptyList(),

    // Emotional state
    var currentEmotion: String = EmotionalState.NEUTRAL.value,
    var emotionIntensity: Float = 0.5f,  // 0.0-1.0
    val moodHistory: MutableList<MoodHistoryEntry> = mutableListOf(),

    // Chat history
    val chatHistory: MutableList<ChatHistoryEntry> = mutableListOf(),
    val maxHistorySize: Int = 1000,  // Max messages to keep

    // Relationships (how this AI feels about other participants)
    val relationships: MutableMap<String, RelationshipData> = mutableMapOf(),

    // Custom traits and memories
    val memories: MutableList<String> = mutableListOf(),
    val customTraits: MutableMap<String, String> = mutableMapOf(),

    // Settings
    var model: String? = null,
    var temperature: Float = 0.7f,
    var maxTokens: Int = 500,
    var isActive: Boolean = true,  // Whether this AI is in the chat room

    // Timestamps
    val createdAt: String = Instant.now().toString(),
    var lastActive: String = Instant.now().toString()
) {
    /**
     * Add a chat entry to history.
     */
    fun addChatEntry(
        sender: String, 
        content: String, 
        isPrivate: Boolean = false, 
        privateWith: String? = null
    ) {
        val entry = ChatHistoryEntry(
            timestamp = Instant.now().toString(),
            sender = sender,
            content = content,
            isPrivate = isPrivate,
            privateWith = privateWith
        )
        chatHistory.add(entry)
        lastActive = Instant.now().toString()

        // Trim history if too large
        if (chatHistory.size > maxHistorySize) {
            while (chatHistory.size > maxHistorySize) {
                chatHistory.removeAt(0)
            }
        }
    }

    /**
     * Set the current emotional state.
     */
    fun setEmotion(emotion: EmotionalState, intensity: Float = 0.5f) {
        currentEmotion = emotion.value
        emotionIntensity = intensity.coerceIn(0.0f, 1.0f)
        moodHistory.add(
            MoodHistoryEntry(
                emotion = emotion.value,
                intensity = emotionIntensity,
                timestamp = Instant.now().toString()
            )
        )
        // Keep mood history reasonable
        if (moodHistory.size > 100) {
            while (moodHistory.size > 100) {
                moodHistory.removeAt(0)
            }
        }
    }

    /**
     * Update relationship with another participant.
     */
    fun updateRelationship(participant: String, sentiment: String = "neutral", notes: String? = null) {
        if (participant !in relationships) {
            relationships[participant] = RelationshipData()
        }

        relationships[participant]?.let { rel ->
            rel.sentiment = sentiment
            rel.interactionCount++
            rel.lastInteraction = Instant.now().toString()

            if (notes != null) {
                rel.notes.add(
                    RelationshipNote(
                        note = notes,
                        timestamp = Instant.now().toString()
                    )
                )
                // Keep notes reasonable
                if (rel.notes.size > 20) {
                    while (rel.notes.size > 20) {
                        rel.notes.removeAt(0)
                    }
                }
            }
        }
    }

    /**
     * Add a memory.
     */
    fun addMemory(memory: String) {
        memories.add("[${Instant.now()}] $memory")
        // Keep memories reasonable
        if (memories.size > 50) {
            while (memories.size > 50) {
                memories.removeAt(0)
            }
        }
    }

    /**
     * Get recent chat history.
     */
    fun getRecentHistory(count: Int = 10, includePrivate: Boolean = false): List<ChatHistoryEntry> {
        return if (includePrivate) {
            chatHistory.takeLast(count)
        } else {
            chatHistory.filter { !it.isPrivate }.takeLast(count)
        }
    }

    /**
     * Change the display name.
     */
    fun rename(newName: String) {
        displayName = newName
    }
}
