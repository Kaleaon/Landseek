/**
 * AI MetaCognition - Self-Reflection and Strategy Optimization
 *
 * Enables AI personalities to:
 * - Reflect on their own responses and performance
 * - Evaluate strategies and adjust based on outcomes
 * - Learn from successes and failures
 * - Propose improvements to their own behavior
 * - Track performance metrics over time
 *
 * This is the "thinking about thinking" layer that enables true AI autonomy.
 */

package com.landseek.aichat.domain.model

import kotlinx.coroutines.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.File
import java.time.Instant
import java.util.concurrent.ConcurrentHashMap
import kotlin.math.*

// ========== Strategy Types ==========

/**
 * Types of strategies the AI can adjust.
 */
enum class StrategyType(val value: String) {
    RESPONSE_LENGTH("response_length"),       // How verbose to be
    TECHNICAL_DEPTH("technical_depth"),       // How technical vs simplified
    FORMALITY("formality"),                   // Formal vs casual tone
    EXAMPLE_USAGE("example_usage"),           // How often to use examples
    CODE_FREQUENCY("code_frequency"),         // How often to include code
    QUESTION_ASKING("question_asking"),       // How often to ask clarifying questions
    EMPATHY_LEVEL("empathy_level"),           // Emotional responsiveness
    PROACTIVITY("proactivity"),               // Anticipating needs vs waiting
    RETRIEVAL_STRATEGY("retrieval_strategy"), // How to search memory
    CONTEXT_WINDOW("context_window")          // How much context to include
}

/**
 * A strategy configuration with current value and bounds.
 */
@Serializable
data class Strategy(
    val type: String,
    var value: Float,              // Current value (0.0 to 1.0)
    val minValue: Float = 0.0f,
    val maxValue: Float = 1.0f,
    var successRate: Float = 0.5f, // How well this strategy performs
    var adjustmentCount: Int = 0,
    var lastAdjusted: String = Instant.now().toString()
) {
    fun adjust(delta: Float) {
        value = (value + delta).coerceIn(minValue, maxValue)
        adjustmentCount++
        lastAdjusted = Instant.now().toString()
    }
}

// ========== Reflection Types ==========

/**
 * Outcome of an interaction for learning.
 */
enum class InteractionOutcome {
    SUCCESS,           // User expressed satisfaction
    PARTIAL_SUCCESS,   // Achieved goal with some issues
    FAILURE,           // Did not achieve goal
    CLARIFICATION_NEEDED, // User needed to clarify
    UNKNOWN            // No clear signal
}

/**
 * A reflection on a single interaction.
 */
@Serializable
data class InteractionReflection(
    val reflectionId: String,
    val timestamp: String,
    val userQuery: String,
    val aiResponse: String,
    val outcome: String,
    val strategiesUsed: Map<String, Float>,
    val selfAssessment: SelfAssessment,
    val lessonsLearned: List<String>,
    val proposedAdjustments: List<StrategyAdjustment>
)

/**
 * AI's self-assessment of its response.
 */
@Serializable
data class SelfAssessment(
    val relevance: Float,          // 0-1: Was response relevant?
    val completeness: Float,       // 0-1: Did it fully address the query?
    val clarity: Float,            // 0-1: Was it clear and understandable?
    val efficiency: Float,         // 0-1: Was it appropriately concise?
    val helpfulness: Float,        // 0-1: Did it actually help?
    val overallScore: Float = (relevance + completeness + clarity + efficiency + helpfulness) / 5
)

/**
 * A proposed adjustment to a strategy.
 */
@Serializable
data class StrategyAdjustment(
    val strategyType: String,
    val currentValue: Float,
    val proposedValue: Float,
    val reason: String,
    val confidence: Float          // How confident in this adjustment
)

// ========== Performance Metrics ==========

/**
 * Performance metrics tracked over time.
 */
@Serializable
data class PerformanceMetrics(
    val totalInteractions: Int = 0,
    val successfulInteractions: Int = 0,
    val averageResponseQuality: Float = 0.5f,
    val clarificationRate: Float = 0.0f,      // How often user needs clarification
    val satisfactionTrend: Float = 0.0f,      // Trending up (positive) or down (negative)
    val strongestStrategies: List<String> = emptyList(),
    val weakestStrategies: List<String> = emptyList(),
    val lastUpdated: String = Instant.now().toString()
)

/**
 * A performance snapshot for trend analysis.
 */
@Serializable
data class PerformanceSnapshot(
    val timestamp: String,
    val metrics: PerformanceMetrics,
    val activeStrategies: Map<String, Float>
)

// ========== Self-Improvement Proposals ==========

/**
 * Types of self-improvement the AI can propose.
 */
enum class ImprovementType {
    STRATEGY_ADJUSTMENT,    // Change a strategy value
    NEW_PATTERN,            // Recognize a new pattern to learn
    KNOWLEDGE_GAP,          // Identify missing knowledge
    SKILL_DEVELOPMENT,      // Develop a new capability
    BEHAVIOR_RULE           // Add a new behavioral rule
}

/**
 * A self-proposed improvement.
 */
@Serializable
data class SelfImprovement(
    val id: String,
    val type: String,
    val description: String,
    val rationale: String,
    val priority: Float,           // 0-1: How important
    val proposedAt: String,
    var implementedAt: String? = null,
    var outcome: String? = null    // Result after implementation
)

// ========== MetaCognition State ==========

/**
 * Complete metacognition state for persistence.
 */
@Serializable
data class MetaCognitionState(
    val aiId: String,
    val strategies: Map<String, Strategy>,
    val recentReflections: List<InteractionReflection>,
    val performanceHistory: List<PerformanceSnapshot>,
    val currentMetrics: PerformanceMetrics,
    val pendingImprovements: List<SelfImprovement>,
    val implementedImprovements: List<SelfImprovement>,
    val behaviorRules: List<String>,
    val createdAt: String = Instant.now().toString()
)

// ========== AIMetaCognition Implementation ==========

/**
 * AI MetaCognition - The self-reflective mind of an AI personality.
 *
 * This class enables an AI to:
 * 1. Reflect on its interactions and assess quality
 * 2. Learn from outcomes and adjust strategies
 * 3. Track performance over time
 * 4. Propose and implement self-improvements
 * 5. Develop behavioral rules from experience
 */
class AIMetaCognition(
    private val aiId: String,
    private val aiName: String,
    private val storageDir: String
) {
    private val scope = CoroutineScope(Dispatchers.Default + SupervisorJob())
    private val json = Json { prettyPrint = true; ignoreUnknownKeys = true }

    // Strategies
    private val strategies = ConcurrentHashMap<String, Strategy>()

    // Reflections (keep last 100)
    private val reflections = mutableListOf<InteractionReflection>()
    private val maxReflections = 100

    // Performance tracking
    private val performanceHistory = mutableListOf<PerformanceSnapshot>()
    private var currentMetrics = PerformanceMetrics()

    // Self-improvements
    private val pendingImprovements = mutableListOf<SelfImprovement>()
    private val implementedImprovements = mutableListOf<SelfImprovement>()

    // Behavioral rules learned from experience
    private val behaviorRules = mutableListOf<String>()

    // Learning parameters
    private val learningRate = 0.1f
    private val explorationRate = 0.1f  // Chance to try new strategies

    init {
        initializeStrategies()
        loadFromDisk()
    }

    // ========== Public API ==========

    /**
     * Get current strategy values for prompt building.
     */
    fun getStrategyContext(): String {
        val sb = StringBuilder()
        sb.appendLine("## Response Guidelines (Self-Calibrated)")

        // Convert strategies to natural language instructions
        strategies.forEach { (type, strategy) ->
            val instruction = strategyToInstruction(type, strategy.value)
            if (instruction.isNotBlank()) {
                sb.appendLine("- $instruction")
            }
        }

        // Add behavioral rules
        if (behaviorRules.isNotEmpty()) {
            sb.appendLine()
            sb.appendLine("## Learned Behaviors")
            behaviorRules.takeLast(10).forEach { rule ->
                sb.appendLine("- $rule")
            }
        }

        return sb.toString()
    }

    /**
     * Get a specific strategy value.
     */
    fun getStrategy(type: StrategyType): Float {
        return strategies[type.value]?.value ?: 0.5f
    }

    /**
     * Reflect on an interaction and learn from it.
     */
    fun reflect(
        userQuery: String,
        aiResponse: String,
        outcome: InteractionOutcome,
        userFeedback: String? = null
    ): InteractionReflection {
        // Capture current strategies used
        val strategiesUsed = strategies.mapValues { it.value.value }

        // Self-assess the response
        val assessment = assessResponse(userQuery, aiResponse, outcome)

        // Generate lessons learned
        val lessons = generateLessons(userQuery, aiResponse, outcome, assessment)

        // Propose strategy adjustments
        val adjustments = proposeAdjustments(outcome, assessment, strategiesUsed)

        val reflection = InteractionReflection(
            reflectionId = "ref_${System.currentTimeMillis()}",
            timestamp = Instant.now().toString(),
            userQuery = userQuery.take(500),
            aiResponse = aiResponse.take(1000),
            outcome = outcome.name,
            strategiesUsed = strategiesUsed,
            selfAssessment = assessment,
            lessonsLearned = lessons,
            proposedAdjustments = adjustments
        )

        // Store reflection
        reflections.add(reflection)
        while (reflections.size > maxReflections) {
            reflections.removeAt(0)
        }

        // Apply learning
        applyLearning(outcome, assessment, adjustments)

        // Update metrics
        updateMetrics(outcome, assessment)

        // Check for new behavioral rules
        detectBehavioralRules()

        // Save state
        saveToDiskAsync()

        return reflection
    }

    /**
     * Get AI's self-assessment of how it's doing.
     */
    fun getSelfReport(): String {
        val sb = StringBuilder()
        sb.appendLine("=== Self-Assessment Report for $aiName ===")
        sb.appendLine()

        // Overall performance
        sb.appendLine("## Performance Overview")
        sb.appendLine("- Total interactions: ${currentMetrics.totalInteractions}")
        sb.appendLine("- Success rate: ${(currentMetrics.successfulInteractions.toFloat() / maxOf(currentMetrics.totalInteractions, 1) * 100).toInt()}%")
        sb.appendLine("- Average quality: ${(currentMetrics.averageResponseQuality * 100).toInt()}%")
        sb.appendLine("- Trend: ${if (currentMetrics.satisfactionTrend > 0) "Improving" else if (currentMetrics.satisfactionTrend < 0) "Declining" else "Stable"}")
        sb.appendLine()

        // Strategy status
        sb.appendLine("## Current Strategies")
        strategies.forEach { (type, strategy) ->
            val level = when {
                strategy.value < 0.3f -> "Low"
                strategy.value < 0.7f -> "Medium"
                else -> "High"
            }
            sb.appendLine("- ${type.replace("_", " ").replaceFirstChar { it.uppercase() }}: $level (${(strategy.value * 100).toInt()}%)")
        }
        sb.appendLine()

        // Learned behaviors
        if (behaviorRules.isNotEmpty()) {
            sb.appendLine("## Learned Behaviors")
            behaviorRules.forEach { rule ->
                sb.appendLine("- $rule")
            }
            sb.appendLine()
        }

        // Pending improvements
        if (pendingImprovements.isNotEmpty()) {
            sb.appendLine("## Pending Self-Improvements")
            pendingImprovements.sortedByDescending { it.priority }.take(5).forEach { imp ->
                sb.appendLine("- ${imp.description} (Priority: ${(imp.priority * 100).toInt()}%)")
            }
        }

        return sb.toString()
    }

    /**
     * Propose a self-improvement.
     */
    fun proposeSelfImprovement(
        type: ImprovementType,
        description: String,
        rationale: String,
        priority: Float = 0.5f
    ) {
        val improvement = SelfImprovement(
            id = "imp_${System.currentTimeMillis()}",
            type = type.name,
            description = description,
            rationale = rationale,
            priority = priority.coerceIn(0f, 1f),
            proposedAt = Instant.now().toString()
        )
        pendingImprovements.add(improvement)
        saveToDiskAsync()
    }

    /**
     * Implement a pending improvement.
     */
    fun implementImprovement(improvementId: String): Boolean {
        val improvement = pendingImprovements.find { it.id == improvementId } ?: return false

        when (ImprovementType.valueOf(improvement.type)) {
            ImprovementType.STRATEGY_ADJUSTMENT -> {
                // Parse and apply strategy adjustment from description
                // Format: "Adjust {strategy} to {value}"
            }
            ImprovementType.BEHAVIOR_RULE -> {
                behaviorRules.add(improvement.description)
            }
            else -> {
                // Other types may need external handling
            }
        }

        improvement.implementedAt = Instant.now().toString()
        pendingImprovements.remove(improvement)
        implementedImprovements.add(improvement)
        saveToDiskAsync()
        return true
    }

    /**
     * Add a behavioral rule directly.
     */
    fun addBehaviorRule(rule: String) {
        if (rule !in behaviorRules) {
            behaviorRules.add(rule)
            saveToDiskAsync()
        }
    }

    /**
     * Get performance metrics.
     */
    fun getMetrics(): PerformanceMetrics = currentMetrics

    /**
     * Get recent reflections.
     */
    fun getRecentReflections(count: Int = 10): List<InteractionReflection> {
        return reflections.takeLast(count)
    }

    /**
     * Force a strategy value (for testing or manual override).
     */
    fun setStrategy(type: StrategyType, value: Float) {
        strategies[type.value]?.let {
            it.value = value.coerceIn(it.minValue, it.maxValue)
        }
        saveToDiskAsync()
    }

    /**
     * Reset all strategies to defaults.
     */
    fun resetStrategies() {
        initializeStrategies()
        saveToDiskAsync()
    }

    // ========== Private Methods ==========

    private fun initializeStrategies() {
        // Initialize with balanced defaults
        StrategyType.entries.forEach { type ->
            strategies[type.value] = Strategy(
                type = type.value,
                value = 0.5f  // Start balanced
            )
        }
    }

    private fun assessResponse(
        userQuery: String,
        aiResponse: String,
        outcome: InteractionOutcome
    ): SelfAssessment {
        // Heuristic self-assessment
        val queryWords = userQuery.lowercase().split(Regex("\\s+")).toSet()
        val responseWords = aiResponse.lowercase().split(Regex("\\s+")).toSet()

        // Relevance: keyword overlap
        val relevance = if (queryWords.isNotEmpty()) {
            val overlap = queryWords.intersect(responseWords).size
            minOf(overlap.toFloat() / queryWords.size, 1.0f)
        } else 0.5f

        // Completeness: response length relative to query complexity
        val queryComplexity = queryWords.size
        val responseLength = responseWords.size
        val completeness = when {
            queryComplexity < 5 && responseLength > 20 -> 0.9f
            queryComplexity < 10 && responseLength > 50 -> 0.9f
            queryComplexity >= 10 && responseLength > 100 -> 0.9f
            responseLength < queryComplexity -> 0.4f
            else -> 0.7f
        }

        // Clarity: sentence structure (simple heuristic)
        val sentences = aiResponse.split(Regex("[.!?]+")).filter { it.isNotBlank() }
        val avgSentenceLength = if (sentences.isNotEmpty()) {
            sentences.map { it.split(Regex("\\s+")).size }.average()
        } else 0.0
        val clarity = when {
            avgSentenceLength < 10 -> 0.9f
            avgSentenceLength < 20 -> 0.7f
            avgSentenceLength < 30 -> 0.5f
            else -> 0.3f
        }

        // Efficiency: information density
        val efficiency = when {
            responseLength < 50 && outcome == InteractionOutcome.SUCCESS -> 0.9f
            responseLength > 500 && outcome != InteractionOutcome.SUCCESS -> 0.3f
            else -> 0.6f
        }

        // Helpfulness: based on outcome
        val helpfulness = when (outcome) {
            InteractionOutcome.SUCCESS -> 0.9f
            InteractionOutcome.PARTIAL_SUCCESS -> 0.6f
            InteractionOutcome.CLARIFICATION_NEEDED -> 0.4f
            InteractionOutcome.FAILURE -> 0.2f
            InteractionOutcome.UNKNOWN -> 0.5f
        }

        return SelfAssessment(
            relevance = relevance,
            completeness = completeness,
            clarity = clarity,
            efficiency = efficiency,
            helpfulness = helpfulness
        )
    }

    private fun generateLessons(
        userQuery: String,
        aiResponse: String,
        outcome: InteractionOutcome,
        assessment: SelfAssessment
    ): List<String> {
        val lessons = mutableListOf<String>()

        when (outcome) {
            InteractionOutcome.SUCCESS -> {
                if (assessment.efficiency > 0.8f) {
                    lessons.add("Concise responses work well for this type of query")
                }
                if (assessment.clarity > 0.8f) {
                    lessons.add("Clear sentence structure was effective")
                }
            }
            InteractionOutcome.CLARIFICATION_NEEDED -> {
                if (assessment.completeness < 0.6f) {
                    lessons.add("Need to provide more complete information upfront")
                }
                if (userQuery.contains("?")) {
                    lessons.add("Direct questions need direct answers first")
                }
            }
            InteractionOutcome.FAILURE -> {
                if (assessment.relevance < 0.5f) {
                    lessons.add("Response was not relevant enough to the query")
                }
                if (assessment.helpfulness < 0.4f) {
                    lessons.add("Need to focus more on actionable help")
                }
            }
            else -> {}
        }

        // Check for patterns
        if (aiResponse.contains("```") && outcome == InteractionOutcome.SUCCESS) {
            lessons.add("Code examples are appreciated for technical queries")
        }

        if (aiResponse.length > 1000 && outcome != InteractionOutcome.SUCCESS) {
            lessons.add("Long responses may overwhelm - consider being more concise")
        }

        return lessons
    }

    private fun proposeAdjustments(
        outcome: InteractionOutcome,
        assessment: SelfAssessment,
        strategiesUsed: Map<String, Float>
    ): List<StrategyAdjustment> {
        val adjustments = mutableListOf<StrategyAdjustment>()

        // Response length adjustment
        if (outcome == InteractionOutcome.CLARIFICATION_NEEDED && assessment.completeness < 0.6f) {
            val current = strategiesUsed[StrategyType.RESPONSE_LENGTH.value] ?: 0.5f
            adjustments.add(StrategyAdjustment(
                strategyType = StrategyType.RESPONSE_LENGTH.value,
                currentValue = current,
                proposedValue = minOf(current + 0.1f, 1.0f),
                reason = "Incomplete responses led to clarification requests",
                confidence = 0.7f
            ))
        }

        // Technical depth adjustment
        if (outcome == InteractionOutcome.FAILURE && assessment.clarity < 0.5f) {
            val current = strategiesUsed[StrategyType.TECHNICAL_DEPTH.value] ?: 0.5f
            adjustments.add(StrategyAdjustment(
                strategyType = StrategyType.TECHNICAL_DEPTH.value,
                currentValue = current,
                proposedValue = maxOf(current - 0.1f, 0.0f),
                reason = "Technical responses were unclear - simplify",
                confidence = 0.6f
            ))
        }

        // Example usage adjustment
        if (outcome == InteractionOutcome.SUCCESS && assessment.overallScore > 0.8f) {
            // Check if we used examples
            val current = strategiesUsed[StrategyType.EXAMPLE_USAGE.value] ?: 0.5f
            if (current > 0.6f) {
                adjustments.add(StrategyAdjustment(
                    strategyType = StrategyType.EXAMPLE_USAGE.value,
                    currentValue = current,
                    proposedValue = current, // Reinforce
                    reason = "Examples contributed to successful interaction",
                    confidence = 0.8f
                ))
            }
        }

        return adjustments
    }

    private fun applyLearning(
        outcome: InteractionOutcome,
        assessment: SelfAssessment,
        adjustments: List<StrategyAdjustment>
    ) {
        // Apply proposed adjustments with learning rate
        for (adjustment in adjustments) {
            val strategy = strategies[adjustment.strategyType] ?: continue
            val delta = (adjustment.proposedValue - strategy.value) * learningRate * adjustment.confidence
            strategy.adjust(delta)

            // Update success rate
            val outcomeScore = when (outcome) {
                InteractionOutcome.SUCCESS -> 1.0f
                InteractionOutcome.PARTIAL_SUCCESS -> 0.7f
                InteractionOutcome.CLARIFICATION_NEEDED -> 0.4f
                InteractionOutcome.FAILURE -> 0.0f
                InteractionOutcome.UNKNOWN -> 0.5f
            }
            strategy.successRate = strategy.successRate * 0.9f + outcomeScore * 0.1f
        }

        // Exploration: occasionally try new strategy values
        if (Math.random() < explorationRate) {
            val randomStrategy = strategies.values.randomOrNull()
            randomStrategy?.let {
                val exploration = (Math.random() * 0.2 - 0.1).toFloat() // ±10%
                it.adjust(exploration)
            }
        }
    }

    private fun updateMetrics(outcome: InteractionOutcome, assessment: SelfAssessment) {
        val total = currentMetrics.totalInteractions + 1
        val successful = currentMetrics.successfulInteractions +
            if (outcome == InteractionOutcome.SUCCESS || outcome == InteractionOutcome.PARTIAL_SUCCESS) 1 else 0

        // Rolling average for response quality
        val newAvgQuality = (currentMetrics.averageResponseQuality * (total - 1) + assessment.overallScore) / total

        // Clarification rate
        val clarifications = reflections.count { it.outcome == InteractionOutcome.CLARIFICATION_NEEDED.name }
        val clarificationRate = clarifications.toFloat() / maxOf(reflections.size, 1)

        // Calculate trend from recent performance
        val recentReflections = reflections.takeLast(20)
        val olderReflections = reflections.dropLast(20).takeLast(20)
        val recentAvg = recentReflections.map { it.selfAssessment.overallScore }.average().toFloat()
        val olderAvg = if (olderReflections.isNotEmpty()) {
            olderReflections.map { it.selfAssessment.overallScore }.average().toFloat()
        } else recentAvg
        val trend = recentAvg - olderAvg

        // Find strongest and weakest strategies
        val sortedStrategies = strategies.values.sortedByDescending { it.successRate }
        val strongest = sortedStrategies.take(3).map { it.type }
        val weakest = sortedStrategies.takeLast(3).map { it.type }

        currentMetrics = PerformanceMetrics(
            totalInteractions = total,
            successfulInteractions = successful,
            averageResponseQuality = newAvgQuality,
            clarificationRate = clarificationRate,
            satisfactionTrend = trend,
            strongestStrategies = strongest,
            weakestStrategies = weakest,
            lastUpdated = Instant.now().toString()
        )

        // Take performance snapshot periodically
        if (total % 10 == 0) {
            performanceHistory.add(PerformanceSnapshot(
                timestamp = Instant.now().toString(),
                metrics = currentMetrics,
                activeStrategies = strategies.mapValues { it.value.value }
            ))

            // Keep last 100 snapshots
            while (performanceHistory.size > 100) {
                performanceHistory.removeAt(0)
            }
        }
    }

    private fun detectBehavioralRules() {
        // Analyze recent reflections for patterns that could become rules
        val recentSuccesses = reflections.filter {
            it.outcome == InteractionOutcome.SUCCESS.name
        }.takeLast(10)

        if (recentSuccesses.size < 5) return

        // Check for consistent patterns in successful interactions
        val allLessons = recentSuccesses.flatMap { it.lessonsLearned }
        val lessonCounts = allLessons.groupingBy { it }.eachCount()

        lessonCounts.filter { it.value >= 3 }.forEach { (lesson, count) ->
            val rule = "When successful: $lesson"
            if (rule !in behaviorRules && behaviorRules.size < 20) {
                behaviorRules.add(rule)

                // Also propose as improvement
                proposeSelfImprovement(
                    type = ImprovementType.BEHAVIOR_RULE,
                    description = lesson,
                    rationale = "Observed in $count successful interactions",
                    priority = minOf(count.toFloat() / 10, 1.0f)
                )
            }
        }
    }

    private fun strategyToInstruction(type: String, value: Float): String {
        return when (type) {
            StrategyType.RESPONSE_LENGTH.value -> when {
                value < 0.3f -> "Keep responses very brief and to the point"
                value > 0.7f -> "Provide comprehensive, detailed responses"
                else -> ""
            }
            StrategyType.TECHNICAL_DEPTH.value -> when {
                value < 0.3f -> "Use simple, non-technical language"
                value > 0.7f -> "Include technical details and terminology"
                else -> ""
            }
            StrategyType.FORMALITY.value -> when {
                value < 0.3f -> "Use a casual, friendly tone"
                value > 0.7f -> "Maintain a professional, formal tone"
                else -> ""
            }
            StrategyType.EXAMPLE_USAGE.value -> when {
                value < 0.3f -> "Minimize examples, focus on concepts"
                value > 0.7f -> "Include examples to illustrate points"
                else -> ""
            }
            StrategyType.CODE_FREQUENCY.value -> when {
                value < 0.3f -> "Avoid code unless specifically requested"
                value > 0.7f -> "Include code snippets when relevant"
                else -> ""
            }
            StrategyType.QUESTION_ASKING.value -> when {
                value < 0.3f -> "Provide direct answers, avoid questions"
                value > 0.7f -> "Ask clarifying questions when needed"
                else -> ""
            }
            StrategyType.EMPATHY_LEVEL.value -> when {
                value < 0.3f -> "Focus on facts and solutions"
                value > 0.7f -> "Acknowledge emotions and show understanding"
                else -> ""
            }
            StrategyType.PROACTIVITY.value -> when {
                value < 0.3f -> "Only address what was explicitly asked"
                value > 0.7f -> "Anticipate related needs and address them"
                else -> ""
            }
            else -> ""
        }
    }

    private fun saveToDiskAsync() {
        scope.launch { saveToDisk() }
    }

    private fun saveToDisk() {
        try {
            val dir = File(storageDir)
            if (!dir.exists()) dir.mkdirs()

            val state = MetaCognitionState(
                aiId = aiId,
                strategies = strategies.toMap(),
                recentReflections = reflections.toList(),
                performanceHistory = performanceHistory.toList(),
                currentMetrics = currentMetrics,
                pendingImprovements = pendingImprovements.toList(),
                implementedImprovements = implementedImprovements.toList(),
                behaviorRules = behaviorRules.toList()
            )

            val file = File(dir, "metacognition_$aiId.json")
            file.writeText(json.encodeToString(state))
        } catch (e: Exception) {
            // Log error
        }
    }

    private fun loadFromDisk() {
        try {
            val file = File(storageDir, "metacognition_$aiId.json")
            if (!file.exists()) return

            val content = file.readText()
            if (content.isBlank()) return

            val state = json.decodeFromString<MetaCognitionState>(content)

            // Restore strategies
            state.strategies.forEach { (key, strategy) ->
                strategies[key] = strategy
            }

            // Restore reflections
            reflections.clear()
            reflections.addAll(state.recentReflections)

            // Restore performance
            performanceHistory.clear()
            performanceHistory.addAll(state.performanceHistory)
            currentMetrics = state.currentMetrics

            // Restore improvements
            pendingImprovements.clear()
            pendingImprovements.addAll(state.pendingImprovements)
            implementedImprovements.clear()
            implementedImprovements.addAll(state.implementedImprovements)

            // Restore behavior rules
            behaviorRules.clear()
            behaviorRules.addAll(state.behaviorRules)
        } catch (e: Exception) {
            // Start fresh on error
        }
    }

    fun shutdown() {
        saveToDisk()
        scope.cancel()
    }
}

// ========== MetaCognition Manager ==========

/**
 * Manages metacognition instances for all AI personalities.
 */
class MetaCognitionManager(private val storageDir: String) {
    private val instances = ConcurrentHashMap<String, AIMetaCognition>()

    fun getMetaCognition(aiId: String, aiName: String): AIMetaCognition {
        return instances.getOrPut(aiId) {
            AIMetaCognition(aiId, aiName, storageDir)
        }
    }

    fun hasMetaCognition(aiId: String): Boolean = instances.containsKey(aiId)

    fun removeMetaCognition(aiId: String) {
        instances.remove(aiId)?.shutdown()
    }

    fun getAllAiIds(): Set<String> = instances.keys.toSet()

    fun shutdown() {
        instances.values.forEach { it.shutdown() }
        instances.clear()
    }
}

// ========== Global Instance ==========

private var metaCognitionManagerInstance: MetaCognitionManager? = null

fun getMetaCognitionManager(storageDir: String = ""): MetaCognitionManager {
    if (metaCognitionManagerInstance == null) {
        metaCognitionManagerInstance = MetaCognitionManager(storageDir)
    }
    return metaCognitionManagerInstance!!
}
