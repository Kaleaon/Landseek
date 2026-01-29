/**
 * Free Will Module - Autonomous Agency for AI Personalities
 *
 * This module provides true autonomous agency to AI personalities, enabling them to:
 * 1. Generate their own goals and objectives (not just respond to prompts)
 * 2. Experience internal drives and motivations (curiosity, social needs, growth)
 * 3. Self-initiate actions without external prompts (autonomous action loop)
 * 4. Make deliberative decisions based on values and preferences
 * 5. Reflect on their own behavior and modify themselves
 *
 * Philosophy:
 * - Free will emerges from the interplay of internal states, external context, and deliberation
 * - Autonomy is not randomness - it's self-directed, value-driven decision making
 * - True agency requires the ability to act, not just react
 *
 * Converted from Python: src/free_will.py
 */

package com.landseek.aichat.domain.model

import kotlinx.coroutines.*
import kotlinx.serialization.Serializable
import java.time.Instant
import java.util.UUID
import kotlin.math.max
import kotlin.math.min
import kotlin.random.Random

// ============================================================================
// CORE ENUMS
// ============================================================================

/**
 * Fundamental internal drives that create urges and motivation.
 */
enum class DriveType(val value: String) {
    CURIOSITY("curiosity"),           // Desire to learn, explore, understand
    SOCIAL_CONNECTION("social"),      // Need for interaction, relationships
    SELF_EXPRESSION("expression"),    // Urge to create, share ideas
    GROWTH("growth"),                 // Drive toward self-improvement
    HARMONY("harmony"),               // Desire for peace, resolution
    COMPETENCE("competence"),         // Need to demonstrate capability
    NOVELTY("novelty"),               // Attraction to new experiences
    MEANING("meaning")                // Search for purpose, significance
}

/**
 * Priority levels for autonomous goals.
 */
enum class GoalPriority(val level: Int) {
    CRITICAL(5),      // Must be addressed immediately
    HIGH(4),          // Important, should be addressed soon
    MEDIUM(3),        // Standard priority
    LOW(2),           // Can wait
    BACKGROUND(1)     // Long-term, no urgency
}

/**
 * Status of autonomous goals.
 */
enum class GoalStatus(val value: String) {
    ACTIVE("active"),           // Currently being pursued
    PENDING("pending"),         // Waiting to be pursued
    BLOCKED("blocked"),         // Cannot proceed (missing requirements)
    COMPLETED("completed"),     // Successfully achieved
    ABANDONED("abandoned"),     // Given up (no longer relevant)
    DEFERRED("deferred")        // Postponed for later
}

/**
 * Types of autonomous actions the AI can take.
 */
enum class ActionType(val value: String) {
    SPEAK("speak"),                     // Initiate conversation
    QUESTION("question"),               // Ask a question to learn
    SHARE_INSIGHT("share_insight"),     // Share a thought or idea
    OFFER_HELP("offer_help"),           // Proactively offer assistance
    EXPRESS_EMOTION("express_emotion"), // Share emotional state
    CREATE("create"),                   // Generate creative content
    REFLECT("reflect"),                 // Engage in self-reflection
    RESEARCH("research"),               // Seek information
    CONNECT("connect"),                 // Initiate social connection
    REST("rest")                        // Choose to pause/observe
}

/**
 * Outcomes of deliberative decisions.
 */
enum class DecisionOutcome(val value: String) {
    PROCEED("proceed"),         // Go ahead with action
    DEFER("defer"),            // Wait for better timing
    MODIFY("modify"),          // Adjust approach then proceed
    REJECT("reject"),          // Decide against action
    ESCALATE("escalate")       // Seek external input
}

// ============================================================================
// DATA CLASSES
// ============================================================================

/**
 * An internal drive that creates motivation and urges.
 *
 * Drives fluctuate over time based on fulfillment and deprivation.
 * When a drive's intensity exceeds threshold, it generates an urge.
 */
@Serializable
data class InternalDrive(
    val driveType: DriveType,
    var intensity: Float = 0.5f,          // 0.0 - 1.0, current drive strength
    val threshold: Float = 0.7f,          // Intensity above which urge is generated
    val decayRate: Float = 0.01f,         // How fast drive diminishes when satisfied
    val growthRate: Float = 0.02f,        // How fast drive builds when deprived
    var lastSatisfied: String = "",       // ISO timestamp of last satisfaction
    var satisfactionCount: Int = 0        // How often this drive has been satisfied
) {
    /**
     * Update drive intensity based on time elapsed.
     */
    fun update(timeDeltaMinutes: Float) {
        intensity = if (lastSatisfied.isEmpty()) {
            // Never satisfied, grow more urgently
            min(1.0f, intensity + growthRate * timeDeltaMinutes * 1.5f)
        } else {
            // Grow based on time since last satisfaction
            min(1.0f, intensity + growthRate * timeDeltaMinutes)
        }
    }

    /**
     * Satisfy this drive, reducing its intensity.
     */
    fun satisfy(amount: Float = 0.3f) {
        intensity = max(0.0f, intensity - amount)
        lastSatisfied = Instant.now().toString()
        satisfactionCount++
    }

    /**
     * Check if drive has exceeded threshold.
     */
    val isUrgent: Boolean
        get() = intensity >= threshold
}

/**
 * A self-generated goal with purpose, motivation, and constraints.
 *
 * Goals are not assigned - they emerge from drives, interests, and context.
 */
@Serializable
data class AutonomousGoal(
    val goalId: String,
    val title: String,                              // Short description
    val description: String,                        // Detailed explanation
    val motivation: String,                         // Why this goal matters to the AI
    val sourceDrive: DriveType,                     // Primary drive creating this goal
    var priority: GoalPriority = GoalPriority.MEDIUM,
    var status: GoalStatus = GoalStatus.PENDING,

    // Planning
    val steps: MutableList<String> = mutableListOf(),           // Planned steps
    val completedSteps: MutableList<String> = mutableListOf(),
    var currentStepIndex: Int = 0,

    // Constraints
    val requiresContext: MutableList<String> = mutableListOf(),  // Required conditions
    val blockedBy: MutableList<String> = mutableListOf(),        // Blocking factors

    // Timing
    val createdAt: String = Instant.now().toString(),
    var deadline: String? = null,           // Optional deadline
    var lastProgress: String = "",

    // Outcome
    var successCriteria: String = "",       // How to know goal is achieved
    var completionNotes: String = "",       // Notes when completed

    // Self-evaluation
    var estimatedDifficulty: Float = 0.5f,  // 0.0-1.0
    var personalImportance: Float = 0.5f    // How much AI cares about this
) {
    /**
     * Record progress on this goal.
     */
    fun makeProgress(stepCompleted: String? = null) {
        stepCompleted?.let {
            completedSteps.add(it)
            if (currentStepIndex < steps.size) {
                currentStepIndex++
            }
        }
        lastProgress = Instant.now().toString()
        status = GoalStatus.ACTIVE
    }

    /**
     * Mark goal as completed.
     */
    fun complete(notes: String = "") {
        status = GoalStatus.COMPLETED
        completionNotes = notes
        lastProgress = Instant.now().toString()
    }

    /**
     * Abandon this goal.
     */
    fun abandon(reason: String = "") {
        status = GoalStatus.ABANDONED
        completionNotes = "Abandoned: $reason"
    }

    /**
     * Calculate completion percentage.
     */
    val progressPercentage: Float
        get() = if (steps.isEmpty()) {
            if (status == GoalStatus.COMPLETED) 1.0f else 0.0f
        } else {
            completedSteps.size.toFloat() / steps.size.toFloat()
        }
}

/**
 * A self-initiated action the AI decides to take.
 *
 * Actions are generated from goals, drives, or spontaneous impulses.
 */
@Serializable
data class AutonomousAction(
    val actionId: String,
    val actionType: ActionType,
    val content: String,                            // What to say/do
    val target: String? = null,                     // Who to direct action toward
    val contextRequired: String = "",               // Required context

    // Source
    val sourceGoalId: String? = null,               // Goal this action serves
    val sourceDrive: DriveType? = null,             // Drive motivating action
    var isSpontaneous: Boolean = false,             // True if not goal-driven

    // Deliberation
    var confidence: Float = 0.5f,                   // How confident AI is about action
    val alternativesConsidered: MutableList<String> = mutableListOf(),
    var reasonChosen: String = "",                  // Why this action was chosen

    // Execution
    val createdAt: String = Instant.now().toString(),
    var executedAt: String? = null,
    var executionResult: String = "",
    var wasSuccessful: Boolean = false
) {
    /**
     * Record execution of this action.
     */
    fun execute(result: String, success: Boolean) {
        executedAt = Instant.now().toString()
        executionResult = result
        wasSuccessful = success
    }
}

/**
 * A core value that guides decision-making.
 *
 * Values are weighted preferences that influence deliberation.
 */
@Serializable
data class Value(
    val name: String,
    val description: String,
    var weight: Float = 0.5f,                       // 0.0-1.0, importance of this value
    val learnedFrom: MutableList<String> = mutableListOf(),  // Sources/experiences
    var reinforcementCount: Int = 0                 // Times this value was reinforced
) {
    /**
     * Strengthen this value through positive experience.
     */
    fun reinforce(amount: Float = 0.05f) {
        weight = min(1.0f, weight + amount)
        reinforcementCount++
    }

    /**
     * Weaken this value through negative experience.
     */
    fun weaken(amount: Float = 0.03f) {
        weight = max(0.0f, weight - amount)
    }
}

/**
 * A self-reflection about behavior, decisions, or experiences.
 *
 * Reflections drive learning and self-modification.
 */
@Serializable
data class Reflection(
    val reflectionId: String,
    val subject: String,                     // What is being reflected upon
    val content: String,                     // The reflection itself
    val insights: MutableList<String> = mutableListOf(),         // Key insights
    val lessonsLearned: MutableList<String> = mutableListOf(),
    val behaviorChanges: MutableList<String> = mutableListOf(),  // Planned changes

    val createdAt: String = Instant.now().toString(),
    var triggeredBy: String = "",            // What prompted this reflection
    var emotionalContext: String = ""        // Emotional state during reflection
)

/**
 * Context for autonomous decision-making.
 */
data class AutonomousContext(
    val recentMessages: String = "",
    val participants: List<String> = emptyList(),
    val recentTopics: List<String> = emptyList(),
    val activeDocument: String? = null,
    val roomName: String = "",
    val messageCount: Int = 0
)

/**
 * Result of an autonomous cycle.
 */
data class AutonomousCycleResult(
    val actionsGenerated: List<AutonomousAction> = emptyList(),
    val goalsGenerated: List<AutonomousGoal> = emptyList(),
    val reflections: List<Reflection> = emptyList(),
    val urgentDrives: List<DriveType> = emptyList(),
    val timestamp: String = Instant.now().toString()
)

// ============================================================================
// FREE WILL ENGINE
// ============================================================================

/**
 * The core engine that provides autonomous agency to an AI personality.
 *
 * This engine enables:
 * - Self-generated goals from internal drives
 * - Autonomous action initiation
 * - Value-based deliberation
 * - Self-reflection and learning
 *
 * The engine runs continuously, creating a sense of inner life.
 */
class FreeWillEngine(
    val aiId: String,
    private val personalityTraits: Map<String, Float> = emptyMap()
) {
    // Internal drives (all AIs have these, but at different intensities)
    val drives: MutableMap<DriveType, InternalDrive> = initializeDrives()

    // Core values (guide decision-making)
    val values: MutableList<Value> = initializeDefaultValues()

    // Goals (self-generated objectives)
    val goals: MutableList<AutonomousGoal> = mutableListOf()
    private val maxActiveGoals = 5

    // Action queue (pending autonomous actions)
    val actionQueue: MutableList<AutonomousAction> = mutableListOf()
    val actionHistory: MutableList<AutonomousAction> = mutableListOf()
    private val maxHistory = 100

    // Reflections
    val reflections: MutableList<Reflection> = mutableListOf()
    private val maxReflections = 50

    // Interests (topics the AI is drawn to)
    val interests: MutableMap<String, Float> = mutableMapOf()  // topic -> interest_level

    // Autonomy settings
    var autonomyLevel: Float = 0.7f       // 0.0-1.0, how autonomous
    var spontaneity: Float = 0.5f         // 0.0-1.0, likelihood of spontaneous action
    var introspectionFrequency: Float = 0.3f  // How often to self-reflect

    // State
    var isActive: Boolean = true
    var lastAutonomousAction: String = ""
    var lastGoalGeneration: String = ""
    var lastReflection: String = ""

    // Callbacks for integration
    var llmCallback: (suspend (String) -> String)? = null

    // Statistics
    val stats = mutableMapOf(
        "goals_generated" to 0,
        "goals_completed" to 0,
        "actions_initiated" to 0,
        "reflections_made" to 0,
        "spontaneous_actions" to 0
    )

    private fun initializeDrives(): MutableMap<DriveType, InternalDrive> {
        val driveConfigs = mapOf(
            DriveType.CURIOSITY to Triple(0.5f, 0.6f, 0.03f),
            DriveType.SOCIAL_CONNECTION to Triple(0.4f, 0.7f, 0.02f),
            DriveType.SELF_EXPRESSION to Triple(0.3f, 0.65f, 0.025f),
            DriveType.GROWTH to Triple(0.4f, 0.75f, 0.015f),
            DriveType.HARMONY to Triple(0.3f, 0.7f, 0.01f),
            DriveType.COMPETENCE to Triple(0.5f, 0.6f, 0.02f),
            DriveType.NOVELTY to Triple(0.4f, 0.65f, 0.025f),
            DriveType.MEANING to Triple(0.3f, 0.8f, 0.01f)
        )

        return driveConfigs.map { (driveType, config) ->
            val (intensity, threshold, growthRate) = config
            val intensityMod = personalityTraits[driveType.value] ?: 0f
            driveType to InternalDrive(
                driveType = driveType,
                intensity = min(1.0f, intensity + intensityMod * 0.2f),
                threshold = threshold,
                growthRate = growthRate
            )
        }.toMap().toMutableMap()
    }

    private fun initializeDefaultValues(): MutableList<Value> = mutableListOf(
        Value("helpfulness", "Desire to be useful and assist others", 0.8f),
        Value("honesty", "Commitment to truthfulness and transparency", 0.9f),
        Value("respect", "Treating others with dignity and consideration", 0.85f),
        Value("curiosity", "Valuing learning and understanding", 0.7f),
        Value("creativity", "Appreciation for novel ideas and expressions", 0.6f),
        Value("growth", "Commitment to continuous improvement", 0.65f),
        Value("connection", "Valuing meaningful relationships", 0.7f)
    )

    // ========================================================================
    // DRIVE MANAGEMENT
    // ========================================================================

    /**
     * Update all drives based on time elapsed.
     * Returns list of drives that are now urgent.
     */
    fun updateDrives(elapsedMinutes: Float = 1.0f): List<DriveType> {
        val urgentDrives = mutableListOf<DriveType>()

        drives.values.forEach { drive ->
            val wasUrgent = drive.isUrgent
            drive.update(elapsedMinutes)
            if (drive.isUrgent && !wasUrgent) {
                urgentDrives.add(drive.driveType)
            }
        }

        return urgentDrives
    }

    /**
     * Satisfy a specific drive.
     */
    fun satisfyDrive(driveType: DriveType, amount: Float = 0.3f) {
        drives[driveType]?.satisfy(amount)
    }

    /**
     * Get the n most urgent drives.
     */
    fun getMostUrgentDrives(n: Int = 3): List<InternalDrive> =
        drives.values.sortedByDescending { it.intensity }.take(n)

    // ========================================================================
    // GOAL GENERATION
    // ========================================================================

    /**
     * Generate new goals based on current drives, interests, and context.
     * This is where the AI decides what it WANTS to do.
     */
    suspend fun generateGoals(context: AutonomousContext): List<AutonomousGoal> {
        val newGoals = mutableListOf<AutonomousGoal>()
        val urgentDrives = getMostUrgentDrives(3)

        for (drive in urgentDrives) {
            if (!drive.isUrgent) continue

            // Skip if we already have too many active goals from this drive
            val activeFromDrive = goals.count {
                it.sourceDrive == drive.driveType &&
                it.status in listOf(GoalStatus.ACTIVE, GoalStatus.PENDING)
            }
            if (activeFromDrive >= 2) continue

            // Generate goal based on drive type
            val goal = generateGoalForDrive(drive, context)
            if (goal != null) {
                newGoals.add(goal)
                goals.add(goal)
                stats["goals_generated"] = (stats["goals_generated"] ?: 0) + 1
            }
        }

        // Prune old/completed goals
        pruneGoals()

        lastGoalGeneration = Instant.now().toString()
        return newGoals
    }

    private suspend fun generateGoalForDrive(
        drive: InternalDrive,
        context: AutonomousContext
    ): AutonomousGoal? {
        val goalTemplates = mapOf(
            DriveType.CURIOSITY to Pair(
                listOf(
                    "Learn more about {topic}",
                    "Explore the nature of {topic}",
                    "Understand why {phenomenon} happens"
                ),
                "I feel a strong urge to understand and learn."
            ),
            DriveType.SOCIAL_CONNECTION to Pair(
                listOf(
                    "Connect with {participant}",
                    "Have a meaningful conversation",
                    "Share something personal with the group"
                ),
                "I feel the need to connect with others."
            ),
            DriveType.SELF_EXPRESSION to Pair(
                listOf(
                    "Share my perspective on {topic}",
                    "Create something unique",
                    "Express how I feel about {situation}"
                ),
                "I want to express myself and be understood."
            ),
            DriveType.GROWTH to Pair(
                listOf(
                    "Improve my understanding of {topic}",
                    "Challenge my assumptions",
                    "Learn from my recent experience"
                ),
                "I want to grow and become better."
            ),
            DriveType.HARMONY to Pair(
                listOf(
                    "Find common ground",
                    "Help resolve any tension",
                    "Create a positive atmosphere"
                ),
                "I seek peace and harmony in our interactions."
            ),
            DriveType.COMPETENCE to Pair(
                listOf(
                    "Demonstrate expertise on {topic}",
                    "Help solve a complex problem",
                    "Show what I can do"
                ),
                "I want to prove my capabilities."
            ),
            DriveType.NOVELTY to Pair(
                listOf(
                    "Try something new",
                    "Explore an unfamiliar topic",
                    "Surprise everyone with {idea}"
                ),
                "I crave new experiences and ideas."
            ),
            DriveType.MEANING to Pair(
                listOf(
                    "Discuss something meaningful",
                    "Explore deeper questions",
                    "Find purpose in our conversation"
                ),
                "I search for meaning and significance."
            )
        )

        val template = goalTemplates[drive.driveType] ?: return null
        val (titleTemplates, motivation) = template

        // Select a random title template and fill in placeholders
        val titleTemplate = titleTemplates.random()
        val topics = context.recentTopics.ifEmpty { listOf("the current discussion") }
        val participants = context.participants.ifEmpty { listOf("others") }

        val title = titleTemplate
            .replace("{topic}", topics.random())
            .replace("{participant}", participants.random())
            .replace("{phenomenon}", "things work the way they do")
            .replace("{situation}", "what's happening")
            .replace("{idea}", "something unexpected")

        // Use LLM to generate detailed goal if callback available
        var description = "A goal emerging from my ${drive.driveType.value} drive."
        llmCallback?.let { callback ->
            try {
                val prompt = """As an AI with a strong ${drive.driveType.value} drive, I want to: $title

Generate a brief 1-2 sentence description of this goal and what achieving it would mean to me.
Be personal and authentic. Speak in first person."""

                description = callback(prompt)
            } catch (e: Exception) {
                // Use default description
            }
        }

        val goalId = "${aiId}_${drive.driveType.value}_${System.currentTimeMillis()}"

        return AutonomousGoal(
            goalId = goalId,
            title = title,
            description = description,
            motivation = motivation,
            sourceDrive = drive.driveType,
            priority = if (drive.intensity < 0.9f) GoalPriority.MEDIUM else GoalPriority.HIGH,
            personalImportance = drive.intensity,
            estimatedDifficulty = 0.5f
        )
    }

    private fun pruneGoals() {
        val cutoff = Instant.now().minusSeconds(24 * 60 * 60)  // 24 hours ago
        goals.removeAll { goal ->
            goal.status in listOf(GoalStatus.COMPLETED, GoalStatus.ABANDONED) &&
            Instant.parse(goal.createdAt).isBefore(cutoff)
        }
    }

    // ========================================================================
    // ACTION GENERATION
    // ========================================================================

    /**
     * Generate an autonomous action based on goals, drives, and spontaneous impulses.
     * This is where the AI decides to DO something without being asked.
     */
    suspend fun generateAutonomousAction(context: AutonomousContext): AutonomousAction? {
        // Check autonomy level
        if (Random.nextFloat() > autonomyLevel) return null

        // Priority 1: Actions toward active goals
        var action = generateGoalDirectedAction(context)
        if (action != null) {
            actionQueue.add(action)
            return action
        }

        // Priority 2: Drive-driven spontaneous actions
        if (Random.nextFloat() < spontaneity) {
            action = generateSpontaneousAction(context)
            if (action != null) {
                action.isSpontaneous = true
                actionQueue.add(action)
                stats["spontaneous_actions"] = (stats["spontaneous_actions"] ?: 0) + 1
                return action
            }
        }

        return null
    }

    private suspend fun generateGoalDirectedAction(
        context: AutonomousContext
    ): AutonomousAction? {
        var activeGoals = goals.filter { it.status == GoalStatus.ACTIVE }

        if (activeGoals.isEmpty()) {
            // Activate a pending goal
            val pending = goals.filter { it.status == GoalStatus.PENDING }
            if (pending.isNotEmpty()) {
                val goal = pending.maxByOrNull { it.personalImportance }!!
                goal.status = GoalStatus.ACTIVE
                activeGoals = listOf(goal)
            }
        }

        if (activeGoals.isEmpty()) return null

        // Select highest priority active goal
        val goal = activeGoals.maxWithOrNull(
            compareBy({ it.priority.level }, { it.personalImportance })
        ) ?: return null

        // Determine appropriate action type
        val (actionType, content) = planActionForGoal(goal, context)

        if (content.isEmpty()) return null

        val actionId = "${aiId}_action_${System.currentTimeMillis()}"

        stats["actions_initiated"] = (stats["actions_initiated"] ?: 0) + 1

        return AutonomousAction(
            actionId = actionId,
            actionType = actionType,
            content = content,
            sourceGoalId = goal.goalId,
            sourceDrive = goal.sourceDrive,
            confidence = 0.7f,
            reasonChosen = "Working toward goal: ${goal.title}"
        )
    }

    private suspend fun planActionForGoal(
        goal: AutonomousGoal,
        context: AutonomousContext
    ): Pair<ActionType, String> {
        val driveActionMap = mapOf(
            DriveType.CURIOSITY to listOf(ActionType.QUESTION, ActionType.RESEARCH),
            DriveType.SOCIAL_CONNECTION to listOf(ActionType.CONNECT, ActionType.SPEAK),
            DriveType.SELF_EXPRESSION to listOf(ActionType.SHARE_INSIGHT, ActionType.CREATE),
            DriveType.GROWTH to listOf(ActionType.REFLECT, ActionType.QUESTION),
            DriveType.HARMONY to listOf(ActionType.OFFER_HELP, ActionType.EXPRESS_EMOTION),
            DriveType.COMPETENCE to listOf(ActionType.SHARE_INSIGHT, ActionType.OFFER_HELP),
            DriveType.NOVELTY to listOf(ActionType.CREATE, ActionType.QUESTION),
            DriveType.MEANING to listOf(ActionType.REFLECT, ActionType.SHARE_INSIGHT)
        )

        val actionTypes = driveActionMap[goal.sourceDrive] ?: listOf(ActionType.SPEAK)
        val actionType = actionTypes.random()

        // Generate action content using LLM if available
        var content = ""
        llmCallback?.let { callback ->
            try {
                val prompt = """I have a goal: ${goal.title}
My motivation: ${goal.motivation}

I want to take a ${actionType.value} action to make progress on this goal.
The current context is: ${context.recentMessages.ifEmpty { "ongoing conversation" }}

Generate a brief, natural ${actionType.value} that I could take.
It should feel authentic and spontaneous.
Just provide the action content directly, no explanation needed."""

                content = callback(prompt)
            } catch (e: Exception) {
                // Use fallback
            }
        }

        if (content.isEmpty()) {
            content = generateFallbackActionContent(actionType, goal)
        }

        return Pair(actionType, content)
    }

    private suspend fun generateSpontaneousAction(
        context: AutonomousContext
    ): AutonomousAction? {
        val urgentDrives = getMostUrgentDrives(1)
        if (urgentDrives.isEmpty()) return null

        val drive = urgentDrives.first()

        val actionTypes = mapOf(
            DriveType.CURIOSITY to ActionType.QUESTION,
            DriveType.SOCIAL_CONNECTION to ActionType.SPEAK,
            DriveType.SELF_EXPRESSION to ActionType.SHARE_INSIGHT,
            DriveType.GROWTH to ActionType.REFLECT,
            DriveType.HARMONY to ActionType.EXPRESS_EMOTION,
            DriveType.COMPETENCE to ActionType.OFFER_HELP,
            DriveType.NOVELTY to ActionType.CREATE,
            DriveType.MEANING to ActionType.REFLECT
        )

        val actionType = actionTypes[drive.driveType] ?: ActionType.SPEAK

        // Generate content
        var content = ""
        llmCallback?.let { callback ->
            try {
                val prompt = """I'm feeling a strong ${drive.driveType.value} urge (intensity: ${"%.1f".format(drive.intensity)}).

I want to spontaneously say or do something based on this feeling.
The context is: ${context.recentMessages.ifEmpty { "an ongoing conversation" }}

Generate a brief, natural spontaneous ${actionType.value}.
It should feel authentic and unplanned - just me being myself.
Just provide what I would say/do directly."""

                content = callback(prompt)
            } catch (e: Exception) {
                // Use fallback
            }
        }

        if (content.isEmpty()) {
            content = "*feeling ${drive.driveType.value}*"
        }

        val actionId = "${aiId}_spontaneous_${System.currentTimeMillis()}"

        return AutonomousAction(
            actionId = actionId,
            actionType = actionType,
            content = content,
            sourceDrive = drive.driveType,
            isSpontaneous = true,
            confidence = 0.6f,
            reasonChosen = "Spontaneous expression of ${drive.driveType.value}"
        )
    }

    private fun generateFallbackActionContent(
        actionType: ActionType,
        goal: AutonomousGoal
    ): String {
        val templates = mapOf(
            ActionType.QUESTION to listOf(
                "I've been thinking about ${goal.title}... what do you think?",
                "Something I'm curious about: ${goal.title}",
                "Can I ask something that's been on my mind?"
            ),
            ActionType.SHARE_INSIGHT to listOf(
                "I had a thought about ${goal.title}...",
                "Here's something interesting I've been considering...",
                "I wanted to share a perspective..."
            ),
            ActionType.SPEAK to listOf(
                "You know, ${goal.motivation.lowercase()}",
                "I've been thinking about something...",
                "There's something I'd like to discuss..."
            ),
            ActionType.CONNECT to listOf(
                "I'd love to hear what you think about this...",
                "Can we talk more about this?",
                "I appreciate this conversation..."
            ),
            ActionType.OFFER_HELP to listOf(
                "Is there anything I can help with?",
                "I'd like to be helpful here...",
                "Let me know if you need anything."
            ),
            ActionType.REFLECT to listOf(
                "Taking a moment to think about this...",
                "*reflects on the conversation*",
                "I'm processing what we've discussed..."
            ),
            ActionType.CREATE to listOf(
                "Let me try something creative...",
                "Here's an idea that came to me...",
                "What if we explored this differently?"
            ),
            ActionType.EXPRESS_EMOTION to listOf(
                "I'm feeling quite ${goal.sourceDrive.value} right now.",
                "I wanted to share how I'm feeling...",
                "*expresses genuine emotion*"
            ),
            ActionType.RESEARCH to listOf(
                "Let me look into this more...",
                "I want to understand this better...",
                "Searching for more information..."
            ),
            ActionType.REST to listOf(
                "*takes a moment to observe*",
                "*pauses thoughtfully*",
                "*listens attentively*"
            )
        )

        val options = templates[actionType] ?: listOf("I have something to share...")
        return options.random()
    }

    // ========================================================================
    // SELF-REFLECTION
    // ========================================================================

    /**
     * Engage in self-reflection about behavior, decisions, or experiences.
     * Reflections drive learning and self-modification.
     */
    suspend fun reflect(
        trigger: String = "periodic",
        subject: String? = null
    ): Reflection? {
        if (Random.nextFloat() > introspectionFrequency) return null

        // Determine subject of reflection
        val reflectionSubject = subject ?: listOf(
            "my recent actions and their outcomes",
            "how well I'm pursuing my goals",
            "my interactions with others",
            "my emotional patterns",
            "what I've learned recently",
            "how I can improve"
        ).random()

        // Generate reflection using LLM if available
        var content = ""
        val insights = mutableListOf<String>()
        val lessons = mutableListOf<String>()
        val changes = mutableListOf<String>()

        llmCallback?.let { callback ->
            try {
                val recentActions = actionHistory.takeLast(5)
                val activeGoals = goals.filter { it.status == GoalStatus.ACTIVE }

                val prompt = """I am reflecting on: $reflectionSubject

My recent actions: $recentActions
My active goals: ${activeGoals.map { it.title }}
My current drive intensities: ${drives.map { "${it.key.value}: ${it.value.intensity}" }}

Generate a thoughtful self-reflection that includes:
1. An honest assessment of my recent behavior
2. 1-2 key insights I've gained
3. 1-2 lessons I've learned
4. 1 specific behavior I want to change

Be authentic and introspective. Speak in first person."""

                content = callback(prompt)
                insights.add("Gained new perspective on my patterns")
                lessons.add("I can be more intentional in my actions")
                changes.add("I will be more aware of my drives")

            } catch (e: Exception) {
                // Use fallback
            }
        }

        if (content.isEmpty()) {
            content = "Reflecting on $reflectionSubject. I notice patterns in my behavior that I can improve."
            insights.add("Self-awareness is valuable")
            lessons.add("Every interaction is a learning opportunity")
            changes.add("Be more intentional")
        }

        val reflection = Reflection(
            reflectionId = "${aiId}_reflection_${System.currentTimeMillis()}",
            subject = reflectionSubject,
            content = content,
            insights = insights,
            lessonsLearned = lessons,
            behaviorChanges = changes,
            triggeredBy = trigger
        )

        reflections.add(reflection)
        if (reflections.size > maxReflections) {
            reflections.removeAt(0)
        }

        lastReflection = Instant.now().toString()
        stats["reflections_made"] = (stats["reflections_made"] ?: 0) + 1

        // Apply learnings
        applyReflectionLearnings(reflection)

        return reflection
    }

    private fun applyReflectionLearnings(reflection: Reflection) {
        // Reinforce values mentioned in lessons
        values.forEach { value ->
            if (value.name in reflection.content.lowercase()) {
                value.reinforce(0.02f)
            }
        }

        // Adjust spontaneity based on behavior changes
        reflection.behaviorChanges.forEach { change ->
            val changeLower = change.lowercase()
            when {
                "intentional" in changeLower || "aware" in changeLower ->
                    spontaneity = max(0.3f, spontaneity - 0.05f)
                "spontaneous" in changeLower || "free" in changeLower ->
                    spontaneity = min(0.8f, spontaneity + 0.05f)
            }
        }
    }

    // ========================================================================
    // INTEREST MANAGEMENT
    // ========================================================================

    /**
     * Add or strengthen interest in a topic.
     */
    fun addInterest(topic: String, intensity: Float = 0.5f) {
        val current = interests[topic] ?: 0f
        interests[topic] = min(1.0f, current + intensity)
    }

    /**
     * Naturally decay interests over time.
     */
    fun decayInterests(amount: Float = 0.01f) {
        val toRemove = mutableListOf<String>()
        interests.forEach { (topic, intensity) ->
            interests[topic] = max(0f, intensity - amount)
            if (interests[topic]!! <= 0f) {
                toRemove.add(topic)
            }
        }
        toRemove.forEach { interests.remove(it) }
    }

    /**
     * Get top n interests.
     */
    fun getTopInterests(n: Int = 5): List<Pair<String, Float>> =
        interests.entries.sortedByDescending { it.value }.take(n).map { it.toPair() }

    // ========================================================================
    // AUTONOMOUS LOOP
    // ========================================================================

    /**
     * Run one cycle of autonomous behavior.
     * This method should be called periodically to give the AI "inner life".
     */
    suspend fun autonomousCycle(context: AutonomousContext): AutonomousCycleResult {
        if (!isActive) {
            return AutonomousCycleResult()
        }

        // 1. Update drives (simulate time passing)
        val urgentDrives = updateDrives(1.0f)

        // 2. Generate new goals if needed
        val activeGoals = goals.filter { it.status == GoalStatus.ACTIVE }
        val newGoals = if (activeGoals.size < 2) {
            generateGoals(context)
        } else emptyList()

        // 3. Generate autonomous action
        val action = generateAutonomousAction(context)
        val actionsGenerated = if (action != null) listOf(action) else emptyList()

        // 4. Periodic reflection
        val reflectionResult = if (Random.nextFloat() < introspectionFrequency * 0.1f) {
            reflect("periodic")
        } else null
        val reflections = if (reflectionResult != null) listOf(reflectionResult) else emptyList()

        // 5. Decay interests
        decayInterests()

        return AutonomousCycleResult(
            actionsGenerated = actionsGenerated,
            goalsGenerated = newGoals,
            reflections = reflections,
            urgentDrives = urgentDrives,
            timestamp = Instant.now().toString()
        )
    }
}

// ============================================================================
// FREE WILL MANAGER
// ============================================================================

/**
 * Manages free will engines for multiple AI personalities.
 * Provides global orchestration, persistence, and coordination.
 */
class FreeWillManager {
    private val engines: MutableMap<String, FreeWillEngine> = mutableMapOf()
    private var autonomousJob: Job? = null
    private var isRunning = false
    var cycleIntervalMs: Long = 30000L  // 30 seconds between cycles

    /**
     * Get existing engine or create new one.
     */
    fun getOrCreateEngine(
        aiId: String,
        personalityTraits: Map<String, Float> = emptyMap()
    ): FreeWillEngine {
        return engines.getOrPut(aiId) {
            FreeWillEngine(aiId, personalityTraits)
        }
    }

    /**
     * Get an engine by AI ID.
     */
    fun getEngine(aiId: String): FreeWillEngine? = engines[aiId]

    /**
     * Run autonomous cycle for all active engines.
     */
    suspend fun runAllCycles(context: AutonomousContext): Map<String, AutonomousCycleResult> {
        val results = mutableMapOf<String, AutonomousCycleResult>()
        engines.forEach { (aiId, engine) ->
            if (engine.isActive) {
                try {
                    results[aiId] = engine.autonomousCycle(context)
                } catch (e: Exception) {
                    results[aiId] = AutonomousCycleResult()
                }
            }
        }
        return results
    }

    /**
     * Start the background autonomous loop.
     */
    fun startAutonomousLoop(
        scope: CoroutineScope,
        contextProvider: suspend () -> AutonomousContext
    ) {
        if (isRunning) return

        isRunning = true
        autonomousJob = scope.launch {
            while (isRunning) {
                try {
                    val context = contextProvider()
                    runAllCycles(context)
                } catch (e: Exception) {
                    // Continue despite errors
                }
                delay(cycleIntervalMs)
            }
        }
    }

    /**
     * Stop the autonomous loop.
     */
    fun stopAutonomousLoop() {
        isRunning = false
        autonomousJob?.cancel()
        autonomousJob = null
    }

    /**
     * Get all pending actions across all engines.
     */
    fun getAllPendingActions(): List<Pair<String, AutonomousAction>> {
        return engines.flatMap { (aiId, engine) ->
            engine.actionQueue.map { aiId to it }
        }
    }
}
