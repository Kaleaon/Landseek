/**
 * Adaptive Memory - Self-Optimizing Memory System with AI-Designed Structures
 *
 * Enables AI personalities to:
 * - Design custom memory schemas based on their needs
 * - Self-optimize retrieval with learned importance weights
 * - Create hierarchical memory with automatic summarization
 * - Use attention-weighted retrieval based on context
 * - Dynamically adjust memory organization
 *
 * This allows each AI to evolve its own optimal memory architecture.
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

// ========== Memory Schema Types ==========

/**
 * A field in a custom memory schema.
 */
@Serializable
data class SchemaField(
    val name: String,
    val type: String,           // "text", "number", "boolean", "list", "embedding"
    val description: String,
    val required: Boolean = false,
    val indexed: Boolean = false,  // Whether to create search index
    val weight: Float = 1.0f       // Importance weight for retrieval
)

/**
 * A custom memory schema designed by the AI.
 */
@Serializable
data class MemorySchema(
    val schemaId: String,
    val name: String,
    val description: String,
    val fields: List<SchemaField>,
    val createdAt: String = Instant.now().toString(),
    var usageCount: Int = 0,
    var successRate: Float = 0.5f,  // How useful retrievals from this schema are
    val parentSchemaId: String? = null  // For hierarchical schemas
)

/**
 * A memory entry conforming to a schema.
 */
@Serializable
data class SchemaMemory(
    val memoryId: String,
    val schemaId: String,
    val data: Map<String, String>,  // Field name -> value (serialized)
    val embedding: List<Float>? = null,
    val importance: Float = 0.5f,
    val accessCount: Int = 0,
    val lastAccessed: String = Instant.now().toString(),
    val createdAt: String = Instant.now().toString(),
    val hierarchyLevel: Int = 0,    // 0 = raw, 1+ = summary levels
    val childIds: List<String> = emptyList()  // For hierarchical memories
)

// ========== Importance Learning ==========

/**
 * Learned importance weights for different memory characteristics.
 */
@Serializable
data class ImportanceWeights(
    var recencyWeight: Float = 0.3f,      // How much recency matters
    var frequencyWeight: Float = 0.2f,    // How much access frequency matters
    var relevanceWeight: Float = 0.4f,    // How much semantic relevance matters
    var sourceWeight: Float = 0.1f,       // How much source type matters
    val sourceTypeWeights: MutableMap<String, Float> = mutableMapOf(
        "conversation" to 0.8f,
        "document" to 0.6f,
        "memory" to 0.9f,
        "summary" to 0.7f,
        "insight" to 0.85f
    )
)

/**
 * Retrieval feedback for learning.
 */
@Serializable
data class RetrievalFeedback(
    val queryId: String,
    val query: String,
    val retrievedIds: List<String>,
    val usefulIds: List<String>,      // Which were actually useful
    val timestamp: String = Instant.now().toString()
)

// ========== Attention Mechanism ==========

/**
 * Attention context for weighted retrieval.
 */
@Serializable
data class AttentionContext(
    val currentTopic: String,
    val recentTopics: List<String>,
    val userIntent: String,           // "question", "task", "chat", "learning"
    val emotionalContext: String,     // "neutral", "frustrated", "curious", etc.
    val timeContext: String           // "immediate", "recent", "historical"
)

/**
 * Attention weights computed for a query.
 */
data class AttentionWeights(
    val topicWeights: Map<String, Float>,
    val schemaWeights: Map<String, Float>,
    val timeDecay: Float,
    val intentBoost: Float
)

// ========== Hierarchical Memory ==========

/**
 * A summary node in the memory hierarchy.
 */
@Serializable
data class MemorySummary(
    val summaryId: String,
    val level: Int,                   // Hierarchy level (1, 2, 3...)
    val content: String,
    val childIds: List<String>,       // IDs of memories/summaries this summarizes
    val topics: List<String>,
    val timeRange: Pair<String, String>,  // Start and end timestamps
    val importance: Float,
    val createdAt: String = Instant.now().toString()
)

// ========== Adaptive Memory State ==========

/**
 * Complete adaptive memory state for persistence.
 */
@Serializable
data class AdaptiveMemoryState(
    val aiId: String,
    val schemas: Map<String, MemorySchema>,
    val memories: Map<String, SchemaMemory>,
    val summaries: Map<String, MemorySummary>,
    val importanceWeights: ImportanceWeights,
    val retrievalHistory: List<RetrievalFeedback>,
    val schemaEvolutionLog: List<SchemaEvolution>,
    val createdAt: String = Instant.now().toString()
)

/**
 * Log entry for schema evolution.
 */
@Serializable
data class SchemaEvolution(
    val timestamp: String,
    val action: String,         // "created", "modified", "merged", "deprecated"
    val schemaId: String,
    val reason: String,
    val performance: Float      // Performance metric at time of change
)

// ========== Adaptive Memory Implementation ==========

/**
 * Adaptive Memory - Self-evolving memory system for AI personalities.
 *
 * Key capabilities:
 * 1. Custom schema design - AI can create memory structures
 * 2. Learned retrieval - Weights are optimized from feedback
 * 3. Hierarchical organization - Automatic summarization layers
 * 4. Attention-weighted search - Context-aware retrieval
 * 5. Schema evolution - Structures adapt over time
 */
class AdaptiveMemory(
    private val aiId: String,
    private val aiName: String,
    private val storageDir: String,
    private val baseEmbedding: SimpleEmbedding = SimpleEmbedding()
) {
    private val scope = CoroutineScope(Dispatchers.Default + SupervisorJob())
    private val json = Json { prettyPrint = true; ignoreUnknownKeys = true }

    // Schemas
    private val schemas = ConcurrentHashMap<String, MemorySchema>()

    // Memories
    private val memories = ConcurrentHashMap<String, SchemaMemory>()

    // Hierarchical summaries
    private val summaries = ConcurrentHashMap<String, MemorySummary>()

    // Learned weights
    private var importanceWeights = ImportanceWeights()

    // Retrieval history for learning
    private val retrievalHistory = mutableListOf<RetrievalFeedback>()
    private val maxRetrievalHistory = 500

    // Schema evolution log
    private val schemaEvolutionLog = mutableListOf<SchemaEvolution>()

    // Learning parameters
    private val learningRate = 0.05f
    private val summarizationThreshold = 20  // Summarize every N memories

    init {
        initializeDefaultSchemas()
        loadFromDisk()
    }

    // ========== Schema Design API ==========

    /**
     * Create a new custom schema.
     * AI can call this to design its own memory structures.
     */
    fun createSchema(
        name: String,
        description: String,
        fields: List<SchemaField>,
        parentSchemaId: String? = null
    ): MemorySchema {
        val schemaId = "schema_${name.lowercase().replace(" ", "_")}_${System.currentTimeMillis()}"

        val schema = MemorySchema(
            schemaId = schemaId,
            name = name,
            description = description,
            fields = fields,
            parentSchemaId = parentSchemaId
        )

        schemas[schemaId] = schema

        schemaEvolutionLog.add(SchemaEvolution(
            timestamp = Instant.now().toString(),
            action = "created",
            schemaId = schemaId,
            reason = "AI-designed schema for: $description",
            performance = 0.5f
        ))

        saveToDiskAsync()
        return schema
    }

    /**
     * Modify an existing schema.
     */
    fun modifySchema(
        schemaId: String,
        addFields: List<SchemaField> = emptyList(),
        removeFields: List<String> = emptyList(),
        updateWeights: Map<String, Float> = emptyMap()
    ): MemorySchema? {
        val schema = schemas[schemaId] ?: return null

        val updatedFields = schema.fields
            .filter { it.name !in removeFields }
            .map { field ->
                if (field.name in updateWeights) {
                    field.copy(weight = updateWeights[field.name]!!)
                } else field
            } + addFields

        val updatedSchema = schema.copy(fields = updatedFields)
        schemas[schemaId] = updatedSchema

        schemaEvolutionLog.add(SchemaEvolution(
            timestamp = Instant.now().toString(),
            action = "modified",
            schemaId = schemaId,
            reason = "Added ${addFields.size} fields, removed ${removeFields.size} fields",
            performance = schema.successRate
        ))

        saveToDiskAsync()
        return updatedSchema
    }

    /**
     * Get suggested schema for a type of memory.
     * AI can use this to get recommendations.
     */
    fun suggestSchema(memoryType: String): MemorySchema? {
        // Find best performing schema for similar types
        return schemas.values
            .filter { it.description.contains(memoryType, ignoreCase = true) }
            .maxByOrNull { it.successRate }
    }

    /**
     * Get all schemas.
     */
    fun getSchemas(): List<MemorySchema> = schemas.values.toList()

    // ========== Memory Storage API ==========

    /**
     * Store a memory using a schema.
     */
    fun store(
        schemaId: String,
        data: Map<String, String>,
        importance: Float = 0.5f
    ): SchemaMemory? {
        val schema = schemas[schemaId] ?: return null

        // Validate required fields
        val requiredFields = schema.fields.filter { it.required }.map { it.name }
        if (!data.keys.containsAll(requiredFields)) {
            return null
        }

        // Generate embedding from text fields
        val textContent = schema.fields
            .filter { it.type == "text" }
            .mapNotNull { data[it.name] }
            .joinToString(" ")

        val embedding = if (textContent.isNotBlank()) {
            baseEmbedding.embed(textContent)
        } else null

        val memoryId = "mem_${schemaId}_${System.currentTimeMillis()}"

        val memory = SchemaMemory(
            memoryId = memoryId,
            schemaId = schemaId,
            data = data,
            embedding = embedding,
            importance = importance
        )

        memories[memoryId] = memory
        schema.usageCount++

        // Check if we need to create summaries
        checkAndSummarize(schemaId)

        saveToDiskAsync()
        return memory
    }

    /**
     * Store using the default schema.
     */
    fun storeSimple(
        content: String,
        source: String,
        sourceType: String,
        importance: Float = 0.5f
    ): SchemaMemory? {
        return store(
            schemaId = "default_memory",
            data = mapOf(
                "content" to content,
                "source" to source,
                "source_type" to sourceType
            ),
            importance = importance
        )
    }

    // ========== Retrieval API ==========

    /**
     * Retrieve memories with learned importance weighting.
     */
    fun retrieve(
        query: String,
        topK: Int = 10,
        schemaFilter: String? = null,
        attentionContext: AttentionContext? = null
    ): List<Pair<SchemaMemory, Float>> {
        val queryId = "query_${System.currentTimeMillis()}"

        // Generate query embedding
        val queryEmbedding = baseEmbedding.embed(query)

        // Compute attention weights if context provided
        val attention = attentionContext?.let { computeAttention(it) }

        // Score all memories
        val scored = memories.values
            .filter { schemaFilter == null || it.schemaId == schemaFilter }
            .map { memory ->
                val score = computeScore(memory, queryEmbedding, attention)
                memory to score
            }
            .sortedByDescending { it.second }
            .take(topK)

        // Record for learning
        retrievalHistory.add(RetrievalFeedback(
            queryId = queryId,
            query = query,
            retrievedIds = scored.map { it.first.memoryId },
            usefulIds = emptyList()  // Will be updated via feedback
        ))

        // Trim history
        while (retrievalHistory.size > maxRetrievalHistory) {
            retrievalHistory.removeAt(0)
        }

        // Update access counts
        scored.forEach { (memory, _) ->
            memories[memory.memoryId] = memory.copy(
                accessCount = memory.accessCount + 1,
                lastAccessed = Instant.now().toString()
            )
        }

        return scored
    }

    /**
     * Retrieve with hierarchical search.
     * Starts with summaries, then drills down.
     */
    fun retrieveHierarchical(
        query: String,
        topK: Int = 10,
        maxDepth: Int = 2
    ): List<Pair<SchemaMemory, Float>> {
        val queryEmbedding = baseEmbedding.embed(query)

        // First, search summaries to find relevant clusters
        val relevantSummaries = summaries.values
            .filter { it.level == 1 }  // Start with first-level summaries
            .map { summary ->
                val summaryEmbedding = baseEmbedding.embed(summary.content)
                val score = baseEmbedding.cosineSimilarity(queryEmbedding, summaryEmbedding)
                summary to score
            }
            .sortedByDescending { it.second }
            .take(3)

        // Get child memory IDs from top summaries
        val candidateIds = relevantSummaries
            .flatMap { it.first.childIds }
            .toSet()

        // Score candidate memories
        return memories.values
            .filter { it.memoryId in candidateIds || candidateIds.isEmpty() }
            .map { memory ->
                val score = computeScore(memory, queryEmbedding, null)
                memory to score
            }
            .sortedByDescending { it.second }
            .take(topK)
    }

    /**
     * Provide feedback on retrieval usefulness.
     */
    fun provideFeedback(queryId: String, usefulMemoryIds: List<String>) {
        val feedback = retrievalHistory.find { it.queryId == queryId } ?: return

        // Update feedback
        val updatedFeedback = feedback.copy(usefulIds = usefulMemoryIds)
        val index = retrievalHistory.indexOf(feedback)
        if (index >= 0) {
            retrievalHistory[index] = updatedFeedback
        }

        // Learn from feedback
        learnFromFeedback(updatedFeedback)

        saveToDiskAsync()
    }

    // ========== Hierarchical Memory ==========

    /**
     * Create a summary of recent memories.
     */
    fun createSummary(
        memoryIds: List<String>,
        level: Int = 1
    ): MemorySummary? {
        val targetMemories = memoryIds.mapNotNull { memories[it] }
        if (targetMemories.isEmpty()) return null

        // Combine content
        val combinedContent = targetMemories.mapNotNull { mem ->
            mem.data["content"]
        }.joinToString("\n")

        // Extract topics (simple keyword extraction)
        val words = combinedContent.lowercase().split(Regex("\\s+"))
        val wordCounts = words.groupingBy { it }.eachCount()
        val topics = wordCounts.entries
            .filter { it.key.length > 4 }
            .sortedByDescending { it.value }
            .take(5)
            .map { it.key }

        // Generate summary content (simple: take key sentences)
        val sentences = combinedContent.split(Regex("[.!?]+")).filter { it.length > 20 }
        val summaryContent = sentences.take(3).joinToString(". ")

        // Calculate importance
        val avgImportance = targetMemories.map { it.importance }.average().toFloat()

        // Get time range
        val timestamps = targetMemories.map { it.createdAt }.sorted()
        val timeRange = Pair(timestamps.first(), timestamps.last())

        val summaryId = "summary_${level}_${System.currentTimeMillis()}"

        val summary = MemorySummary(
            summaryId = summaryId,
            level = level,
            content = summaryContent,
            childIds = memoryIds,
            topics = topics,
            timeRange = timeRange,
            importance = avgImportance
        )

        summaries[summaryId] = summary
        saveToDiskAsync()

        return summary
    }

    /**
     * Get memory hierarchy for inspection.
     */
    fun getHierarchy(): Map<Int, List<MemorySummary>> {
        return summaries.values.groupBy { it.level }
    }

    // ========== Weight Learning ==========

    /**
     * Get current importance weights.
     */
    fun getImportanceWeights(): ImportanceWeights = importanceWeights

    /**
     * Manually adjust weights (for AI to tune itself).
     */
    fun adjustWeights(
        recency: Float? = null,
        frequency: Float? = null,
        relevance: Float? = null,
        source: Float? = null
    ) {
        recency?.let { importanceWeights.recencyWeight = it.coerceIn(0f, 1f) }
        frequency?.let { importanceWeights.frequencyWeight = it.coerceIn(0f, 1f) }
        relevance?.let { importanceWeights.relevanceWeight = it.coerceIn(0f, 1f) }
        source?.let { importanceWeights.sourceWeight = it.coerceIn(0f, 1f) }

        // Normalize
        val total = importanceWeights.recencyWeight + importanceWeights.frequencyWeight +
            importanceWeights.relevanceWeight + importanceWeights.sourceWeight
        if (total > 0) {
            importanceWeights.recencyWeight /= total
            importanceWeights.frequencyWeight /= total
            importanceWeights.relevanceWeight /= total
            importanceWeights.sourceWeight /= total
        }

        saveToDiskAsync()
    }

    // ========== Self-Analysis ==========

    /**
     * Get memory statistics and recommendations.
     */
    fun analyze(): MemoryAnalysis {
        val totalMemories = memories.size
        val totalSummaries = summaries.size

        // Schema usage
        val schemaUsage = schemas.values.associate { it.name to it.usageCount }

        // Schema performance
        val schemaPerformance = schemas.values.associate { it.name to it.successRate }

        // Memory age distribution
        val now = Instant.now().toEpochMilli()
        val ages = memories.values.map {
            (now - Instant.parse(it.createdAt).toEpochMilli()) / (1000 * 60 * 60 * 24)  // Days
        }
        val avgAge = ages.average()

        // Access patterns
        val accessCounts = memories.values.map { it.accessCount }
        val avgAccess = accessCounts.average()
        val neverAccessed = accessCounts.count { it == 0 }

        // Generate recommendations
        val recommendations = mutableListOf<String>()

        if (neverAccessed > totalMemories * 0.3) {
            recommendations.add("Consider pruning ${neverAccessed} never-accessed memories")
        }

        schemas.values.filter { it.successRate < 0.3f && it.usageCount > 10 }.forEach {
            recommendations.add("Schema '${it.name}' has low success rate - consider redesigning")
        }

        if (totalMemories > 100 && totalSummaries < totalMemories / 20) {
            recommendations.add("Create more summaries to improve hierarchical search")
        }

        return MemoryAnalysis(
            totalMemories = totalMemories,
            totalSummaries = totalSummaries,
            schemaUsage = schemaUsage,
            schemaPerformance = schemaPerformance,
            averageMemoryAgeDays = avgAge,
            averageAccessCount = avgAccess,
            neverAccessedCount = neverAccessed,
            recommendations = recommendations,
            currentWeights = importanceWeights
        )
    }

    /**
     * Propose schema improvements based on usage patterns.
     */
    fun proposeSchemaImprovements(): List<SchemaImprovement> {
        val improvements = mutableListOf<SchemaImprovement>()

        // Find underperforming schemas
        schemas.values.filter { it.successRate < 0.4f && it.usageCount > 5 }.forEach { schema ->
            improvements.add(SchemaImprovement(
                schemaId = schema.schemaId,
                type = "redesign",
                description = "Schema '${schema.name}' has ${(schema.successRate * 100).toInt()}% success rate",
                suggestion = "Consider adding more specific fields or splitting into sub-schemas"
            ))
        }

        // Find schemas that could be merged
        val similarSchemas = schemas.values.groupBy { it.fields.map { f -> f.name }.sorted() }
        similarSchemas.filter { it.value.size > 1 }.forEach { (_, group) ->
            improvements.add(SchemaImprovement(
                schemaId = group.first().schemaId,
                type = "merge",
                description = "Schemas ${group.map { it.name }} have identical fields",
                suggestion = "Consider merging into a single schema"
            ))
        }

        return improvements
    }

    // ========== Private Methods ==========

    private fun initializeDefaultSchemas() {
        // Default general memory schema
        val defaultSchema = MemorySchema(
            schemaId = "default_memory",
            name = "General Memory",
            description = "Default schema for general memories",
            fields = listOf(
                SchemaField("content", "text", "The memory content", required = true, indexed = true),
                SchemaField("source", "text", "Where this memory came from"),
                SchemaField("source_type", "text", "Type of source (conversation, document, etc.)"),
                SchemaField("tags", "list", "Tags for categorization")
            )
        )
        schemas[defaultSchema.schemaId] = defaultSchema

        // Conversation memory schema
        val conversationSchema = MemorySchema(
            schemaId = "conversation_memory",
            name = "Conversation Memory",
            description = "Schema for storing conversation excerpts",
            fields = listOf(
                SchemaField("content", "text", "The conversation content", required = true, indexed = true),
                SchemaField("participants", "list", "Who was involved"),
                SchemaField("topic", "text", "Main topic discussed"),
                SchemaField("sentiment", "text", "Overall sentiment"),
                SchemaField("key_points", "list", "Key takeaways")
            )
        )
        schemas[conversationSchema.schemaId] = conversationSchema

        // Insight schema
        val insightSchema = MemorySchema(
            schemaId = "insight_memory",
            name = "Insight Memory",
            description = "Schema for storing insights and learnings",
            fields = listOf(
                SchemaField("insight", "text", "The insight itself", required = true, indexed = true),
                SchemaField("context", "text", "Context in which it was learned"),
                SchemaField("confidence", "number", "Confidence level 0-1"),
                SchemaField("applications", "list", "Where this insight applies")
            )
        )
        schemas[insightSchema.schemaId] = insightSchema
    }

    private fun computeScore(
        memory: SchemaMemory,
        queryEmbedding: List<Float>,
        attention: AttentionWeights?
    ): Float {
        var score = 0f

        // Semantic relevance
        memory.embedding?.let { memEmbedding ->
            val relevance = baseEmbedding.cosineSimilarity(queryEmbedding, memEmbedding)
            score += relevance * importanceWeights.relevanceWeight
        }

        // Recency
        val now = Instant.now().toEpochMilli()
        val memTime = Instant.parse(memory.createdAt).toEpochMilli()
        val ageHours = (now - memTime) / (1000 * 60 * 60).toFloat()
        val recencyScore = exp(-ageHours / (24 * 7)).toFloat()  // Week half-life
        score += recencyScore * importanceWeights.recencyWeight

        // Frequency (access count)
        val frequencyScore = minOf(memory.accessCount / 10f, 1f)
        score += frequencyScore * importanceWeights.frequencyWeight

        // Source type weight
        val sourceType = memory.data["source_type"] ?: "unknown"
        val sourceWeight = importanceWeights.sourceTypeWeights[sourceType] ?: 0.5f
        score += sourceWeight * importanceWeights.sourceWeight

        // Base importance
        score += memory.importance * 0.2f

        // Apply attention if available
        attention?.let { att ->
            // Schema weight
            val schemaWeight = att.schemaWeights[memory.schemaId] ?: 1f
            score *= schemaWeight

            // Time decay
            score *= att.timeDecay

            // Intent boost
            score *= att.intentBoost
        }

        return score
    }

    private fun computeAttention(context: AttentionContext): AttentionWeights {
        // Compute schema weights based on topic
        val schemaWeights = schemas.mapValues { (_, schema) ->
            if (schema.description.contains(context.currentTopic, ignoreCase = true)) 1.5f
            else 1.0f
        }

        // Time decay based on time context
        val timeDecay = when (context.timeContext) {
            "immediate" -> 2.0f   // Boost very recent
            "recent" -> 1.0f     // Normal
            "historical" -> 0.5f  // Allow older memories
            else -> 1.0f
        }

        // Intent boost
        val intentBoost = when (context.userIntent) {
            "question" -> 1.2f   // Boost factual retrieval
            "task" -> 1.1f       // Boost procedural memories
            "learning" -> 1.3f   // Boost insights
            else -> 1.0f
        }

        return AttentionWeights(
            topicWeights = context.recentTopics.associateWith { 1.2f },
            schemaWeights = schemaWeights,
            timeDecay = timeDecay,
            intentBoost = intentBoost
        )
    }

    private fun learnFromFeedback(feedback: RetrievalFeedback) {
        if (feedback.retrievedIds.isEmpty()) return

        val usefulSet = feedback.usefulIds.toSet()
        val retrievedMemories = feedback.retrievedIds.mapNotNull { memories[it] }

        // Calculate what made useful memories different
        val usefulMemories = retrievedMemories.filter { it.memoryId in usefulSet }
        val notUsefulMemories = retrievedMemories.filter { it.memoryId !in usefulSet }

        if (usefulMemories.isEmpty() || notUsefulMemories.isEmpty()) return

        // Compare characteristics
        val usefulAvgRecency = usefulMemories.map {
            Instant.parse(it.createdAt).toEpochMilli()
        }.average()
        val notUsefulAvgRecency = notUsefulMemories.map {
            Instant.parse(it.createdAt).toEpochMilli()
        }.average()

        // Adjust recency weight
        if (usefulAvgRecency > notUsefulAvgRecency) {
            // Recent memories were more useful
            importanceWeights.recencyWeight += learningRate * 0.1f
        } else {
            importanceWeights.recencyWeight -= learningRate * 0.05f
        }

        // Update schema success rates
        usefulMemories.forEach { mem ->
            schemas[mem.schemaId]?.let { schema ->
                schema.successRate = schema.successRate * 0.95f + 0.05f
            }
        }
        notUsefulMemories.forEach { mem ->
            schemas[mem.schemaId]?.let { schema ->
                schema.successRate = schema.successRate * 0.95f
            }
        }

        // Normalize weights
        val total = importanceWeights.recencyWeight + importanceWeights.frequencyWeight +
            importanceWeights.relevanceWeight + importanceWeights.sourceWeight
        if (total > 0) {
            importanceWeights.recencyWeight = (importanceWeights.recencyWeight / total).coerceIn(0.1f, 0.5f)
            importanceWeights.frequencyWeight = (importanceWeights.frequencyWeight / total).coerceIn(0.1f, 0.4f)
            importanceWeights.relevanceWeight = (importanceWeights.relevanceWeight / total).coerceIn(0.2f, 0.6f)
            importanceWeights.sourceWeight = (importanceWeights.sourceWeight / total).coerceIn(0.05f, 0.3f)
        }
    }

    private fun checkAndSummarize(schemaId: String) {
        val schemaMemories = memories.values
            .filter { it.schemaId == schemaId && it.hierarchyLevel == 0 }
            .sortedBy { it.createdAt }

        // Check if we have enough unsummarized memories
        val summarizedIds = summaries.values.flatMap { it.childIds }.toSet()
        val unsummarized = schemaMemories.filter { it.memoryId !in summarizedIds }

        if (unsummarized.size >= summarizationThreshold) {
            // Create summary of oldest unsummarized memories
            val toSummarize = unsummarized.take(summarizationThreshold)
            scope.launch {
                createSummary(toSummarize.map { it.memoryId })
            }
        }
    }

    private fun saveToDiskAsync() {
        scope.launch { saveToDisk() }
    }

    private fun saveToDisk() {
        try {
            val dir = File(storageDir)
            if (!dir.exists()) dir.mkdirs()

            val state = AdaptiveMemoryState(
                aiId = aiId,
                schemas = schemas.toMap(),
                memories = memories.toMap(),
                summaries = summaries.toMap(),
                importanceWeights = importanceWeights,
                retrievalHistory = retrievalHistory.toList(),
                schemaEvolutionLog = schemaEvolutionLog.toList()
            )

            val file = File(dir, "adaptive_memory_$aiId.json")
            file.writeText(json.encodeToString(state))
        } catch (e: Exception) {
            // Log error
        }
    }

    private fun loadFromDisk() {
        try {
            val file = File(storageDir, "adaptive_memory_$aiId.json")
            if (!file.exists()) return

            val content = file.readText()
            if (content.isBlank()) return

            val state = json.decodeFromString<AdaptiveMemoryState>(content)

            schemas.clear()
            schemas.putAll(state.schemas)

            memories.clear()
            memories.putAll(state.memories)

            summaries.clear()
            summaries.putAll(state.summaries)

            importanceWeights = state.importanceWeights

            retrievalHistory.clear()
            retrievalHistory.addAll(state.retrievalHistory)

            schemaEvolutionLog.clear()
            schemaEvolutionLog.addAll(state.schemaEvolutionLog)
        } catch (e: Exception) {
            // Start fresh
        }
    }

    fun shutdown() {
        saveToDisk()
        scope.cancel()
    }
}

// ========== Analysis Types ==========

/**
 * Memory analysis results.
 */
data class MemoryAnalysis(
    val totalMemories: Int,
    val totalSummaries: Int,
    val schemaUsage: Map<String, Int>,
    val schemaPerformance: Map<String, Float>,
    val averageMemoryAgeDays: Double,
    val averageAccessCount: Double,
    val neverAccessedCount: Int,
    val recommendations: List<String>,
    val currentWeights: ImportanceWeights
)

/**
 * Schema improvement suggestion.
 */
data class SchemaImprovement(
    val schemaId: String,
    val type: String,         // "redesign", "merge", "split", "add_field"
    val description: String,
    val suggestion: String
)

// ========== Adaptive Memory Manager ==========

/**
 * Manages adaptive memory instances for all AI personalities.
 */
class AdaptiveMemoryManager(private val storageDir: String) {
    private val instances = ConcurrentHashMap<String, AdaptiveMemory>()

    fun getAdaptiveMemory(aiId: String, aiName: String): AdaptiveMemory {
        return instances.getOrPut(aiId) {
            AdaptiveMemory(aiId, aiName, storageDir)
        }
    }

    fun hasAdaptiveMemory(aiId: String): Boolean = instances.containsKey(aiId)

    fun removeAdaptiveMemory(aiId: String) {
        instances.remove(aiId)?.shutdown()
    }

    fun getAllAiIds(): Set<String> = instances.keys.toSet()

    fun shutdown() {
        instances.values.forEach { it.shutdown() }
        instances.clear()
    }
}

// ========== Global Instance ==========

private var adaptiveMemoryManagerInstance: AdaptiveMemoryManager? = null

fun getAdaptiveMemoryManager(storageDir: String = ""): AdaptiveMemoryManager {
    if (adaptiveMemoryManagerInstance == null) {
        adaptiveMemoryManagerInstance = AdaptiveMemoryManager(storageDir)
    }
    return adaptiveMemoryManagerInstance!!
}
