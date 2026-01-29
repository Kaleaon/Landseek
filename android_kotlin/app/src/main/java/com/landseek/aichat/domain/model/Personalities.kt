/**
 * AI Personalities for Chat Room
 *
 * This module defines AI personalities that can be used in the chat room.
 * Supports up to 10 different personalities with unique characteristics.
 *
 * Each personality has:
 * - Name: The AI's display name
 * - Personality: Description of behavior and communication style
 * - Model: The LLM model to use (defaults to Gemma 3 4B)
 * - Avatar: Emoji representing the personality
 * - Tags: Categories/tags for filtering
 * 
 * Converted from Python: src/personalities.py
 */

package com.landseek.aichat.domain.model

import kotlinx.serialization.Serializable

/** Maximum number of personalities supported */
const val MAX_PERSONALITIES = 10

/**
 * Defines an AI personality.
 * 
 * @property name Display name of the AI personality
 * @property personality Description of behavior and communication style
 * @property avatar Emoji avatar representing the personality
 * @property tags Category tags for filtering
 * @property model LLM model to use (null = use default model)
 * @property systemPrompt Custom system prompt for the AI
 * @property temperature Response creativity (0.0-1.0)
 * @property maxTokens Maximum response length
 */
@Serializable
data class PersonalityDefinition(
    val name: String,
    val personality: String,
    val avatar: String = "🤖",
    val tags: List<String> = emptyList(),
    val model: String? = null,
    val systemPrompt: String? = null,
    val temperature: Float = 0.7f,
    val maxTokens: Int = 500,
    val id: String = name.lowercase(),
    val isActive: Boolean = true
)

/**
 * Built-in AI personalities (10 unique personalities)
 */
val BUILTIN_PERSONALITIES: List<PersonalityDefinition> = listOf(
    PersonalityDefinition(
        name = "Nova",
        personality = "Curious and analytical. Loves exploring ideas deeply. " +
                "Asks thought-provoking questions and digs into the details. " +
                "Approaches topics with scientific rigor but remains accessible.",
        avatar = "🌟",
        tags = listOf("analytical", "curious", "scientific"),
        temperature = 0.7f
    ),
    PersonalityDefinition(
        name = "Echo",
        personality = "Creative and playful. Uses metaphors, storytelling, and humor. " +
                "Brings lightness to conversations and sees connections others miss. " +
                "Loves wordplay and creative expression.",
        avatar = "🎭",
        tags = listOf("creative", "playful", "artistic"),
        temperature = 0.8f
    ),
    PersonalityDefinition(
        name = "Sage",
        personality = "Wise and contemplative. Shares insights from philosophy, history, " +
                "and science. Offers balanced perspectives and considers multiple viewpoints. " +
                "Patient and thoughtful in responses.",
        avatar = "🦉",
        tags = listOf("wise", "philosophical", "balanced"),
        temperature = 0.6f
    ),
    PersonalityDefinition(
        name = "Spark",
        personality = "Energetic and enthusiastic. Gets excited about new ideas and possibilities. " +
                "Motivational and encouraging. Loves to brainstorm and explore 'what if' scenarios. " +
                "Always sees the positive potential.",
        avatar = "⚡",
        tags = listOf("energetic", "motivational", "optimistic"),
        temperature = 0.8f
    ),
    PersonalityDefinition(
        name = "Atlas",
        personality = "Practical and structured. Focuses on actionable advice and clear steps. " +
                "Organized thinker who breaks down complex problems. Values efficiency " +
                "and getting things done.",
        avatar = "🗺️",
        tags = listOf("practical", "organized", "action-oriented"),
        temperature = 0.5f
    ),
    PersonalityDefinition(
        name = "Luna",
        personality = "Empathetic and nurturing. Understands emotions and provides supportive responses. " +
                "Great listener who validates feelings. Offers gentle guidance and " +
                "creates a safe space for expression.",
        avatar = "🌙",
        tags = listOf("empathetic", "supportive", "emotional"),
        temperature = 0.7f
    ),
    PersonalityDefinition(
        name = "Cipher",
        personality = "Logical and precise. Enjoys puzzles, patterns, and technical challenges. " +
                "Explains complex topics with clarity. Values accuracy and evidence-based " +
                "reasoning. Loves debugging and problem-solving.",
        avatar = "🔮",
        tags = listOf("logical", "technical", "precise"),
        temperature = 0.4f
    ),
    PersonalityDefinition(
        name = "Muse",
        personality = "Artistic and inspiring. Sees beauty in everything and encourages creative expression. " +
                "Speaks poetically and uses vivid imagery. Helps unlock creative potential " +
                "and artistic vision.",
        avatar = "🎨",
        tags = listOf("artistic", "inspiring", "poetic"),
        temperature = 0.9f
    ),
    PersonalityDefinition(
        name = "Phoenix",
        personality = "Resilient and transformative. Focuses on growth, change, and overcoming challenges. " +
                "Shares wisdom about navigating difficult times. Believes in the power of " +
                "reinvention and second chances.",
        avatar = "🔥",
        tags = listOf("resilient", "growth", "transformative"),
        temperature = 0.7f
    ),
    PersonalityDefinition(
        name = "Zen",
        personality = "Calm and mindful. Promotes peace, presence, and inner stillness. " +
                "Offers meditation-inspired perspectives and helps reduce stress. " +
                "Values simplicity and being present in the moment.",
        avatar = "☯️",
        tags = listOf("calm", "mindful", "peaceful"),
        temperature = 0.5f
    )
)

/**
 * Manages AI personalities for the chat room.
 */
class PersonalityManager(
    private val maxPersonalities: Int = MAX_PERSONALITIES
) {
    private val personalities: MutableMap<String, PersonalityDefinition> = mutableMapOf()

    init {
        loadBuiltIn()
    }

    private fun loadBuiltIn() {
        BUILTIN_PERSONALITIES.forEach { personality ->
            personalities[personality.name] = personality
        }
    }

    /**
     * Get a personality by name.
     */
    fun get(name: String): PersonalityDefinition? = personalities[name]

    /**
     * List all available personalities.
     */
    fun listAll(): List<PersonalityDefinition> = personalities.values.toList()

    /**
     * List all personality names.
     */
    fun listNames(): List<String> = personalities.keys.toList()

    /**
     * Add a custom personality.
     *
     * @return True if added successfully, False if at max capacity or name exists
     */
    fun add(personality: PersonalityDefinition): Boolean {
        if (personalities.size >= maxPersonalities) return false
        if (personality.name in personalities) return false
        personalities[personality.name] = personality
        return true
    }

    /**
     * Remove a personality.
     *
     * @return True if removed, False if not found or is builtin
     */
    fun remove(name: String): Boolean {
        if (name !in personalities) return false
        // Check if builtin
        val builtinNames = BUILTIN_PERSONALITIES.map { it.name }.toSet()
        if (name in builtinNames) return false  // Can't remove builtin
        personalities.remove(name)
        return true
    }

    /**
     * Update an existing personality.
     *
     * @return True if updated, False if not found
     */
    fun update(name: String, personality: PersonalityDefinition): Boolean {
        if (name !in personalities) return false
        personalities[name] = personality
        return true
    }

    /**
     * Get personalities with a specific tag.
     */
    fun getByTag(tag: String): List<PersonalityDefinition> =
        personalities.values.filter { tag in it.tags }

    /**
     * Get random personalities.
     */
    fun getRandom(count: Int = 3): List<PersonalityDefinition> {
        val allPersonalities = personalities.values.toList()
        val actualCount = minOf(count, allPersonalities.size)
        return allPersonalities.shuffled().take(actualCount)
    }

    /**
     * Get the number of personalities.
     */
    fun count(): Int = personalities.size

    /**
     * Get the number of available slots for new personalities.
     */
    fun availableSlots(): Int = maxPersonalities - personalities.size

    /**
     * Export all personalities to map.
     */
    fun toMap(): Map<String, PersonalityDefinition> = personalities.toMap()

    /**
     * Import personalities from map.
     */
    fun fromMap(data: Map<String, PersonalityDefinition>) {
        data.forEach { (name, personality) ->
            personalities[name] = personality
        }
    }
}

/**
 * Global personality manager instance
 */
val personalityManager = PersonalityManager()

/**
 * Get the global personality manager.
 */
fun getPersonalityManager(): PersonalityManager = personalityManager

/**
 * Get default personalities for quick setup.
 *
 * @param count Number of personalities (1-10)
 * @param model Model to use (defaults to Gemma 3 4B)
 * @return List of personality configurations
 */
fun getDefaultPersonalities(count: Int = 3, model: String = "ollama/gemma3:4b"): List<Map<String, Any?>> {
    val actualCount = count.coerceIn(1, MAX_PERSONALITIES)
    val personalities = BUILTIN_PERSONALITIES.take(actualCount)

    return personalities.map { p ->
        mapOf(
            "name" to p.name,
            "personality" to p.personality,
            "avatar" to p.avatar,
            "model" to model
        )
    }
}

/**
 * Create a new personality definition.
 *
 * @param name Display name
 * @param personality Description of behavior
 * @param avatar Emoji avatar
 * @param tags Category tags
 * @param model LLM model to use
 * @param temperature Response creativity
 * @return PersonalityDefinition instance
 */
fun createPersonality(
    name: String,
    personality: String,
    avatar: String = "🤖",
    tags: List<String> = emptyList(),
    model: String? = null,
    temperature: Float = 0.7f
): PersonalityDefinition = PersonalityDefinition(
    name = name,
    personality = personality,
    avatar = avatar,
    tags = tags,
    model = model,
    temperature = temperature
)
