/**
 * RLM (Recursive Language Model) - Core Implementation
 *
 * This module provides the Recursive Language Model implementation for
 * iterative AI reasoning with:
 * - Safe REPL code execution
 * - Recursive reasoning loops
 * - Tool/function calling
 * - RAG integration
 *
 * Converted from Python: src/rlm/core.py, parser.py, prompts.py, repl.py, types.py
 */

package com.landseek.aichat.domain.model

import kotlinx.coroutines.*
import kotlinx.serialization.Serializable
import java.time.Instant
import retrofit2.Call
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.POST
import com.google.gson.annotations.SerializedName

// ========== Types (from types.py) ==========

/**
 * Message role in a conversation.
 */
enum class MessageRole(val value: String) {
    SYSTEM("system"),
    USER("user"),
    ASSISTANT("assistant"),
    TOOL("tool")
}

/**
 * A message in a conversation.
 */
@Serializable
data class RLMMessage(
    val role: String,
    val content: String,
    val name: String? = null,
    val toolCallId: String? = null
)

/**
 * Tool call request.
 */
@Serializable
data class ToolCall(
    val id: String,
    val name: String,
    val arguments: Map<String, String>
)

/**
 * Tool call result.
 */
@Serializable
data class ToolCallResult(
    val id: String,
    val name: String,
    val result: String,
    val success: Boolean
)

// ========== REPL (from repl.py) ==========

/**
 * Error during REPL execution.
 */
class REPLError(message: String) : Exception(message)

/**
 * Safe REPL executor for code evaluation.
 */
class REPLExecutor {
    // Allowed operations for safety
    private val allowedOperations = setOf(
        "add", "subtract", "multiply", "divide",
        "sqrt", "pow", "sin", "cos", "tan",
        "log", "exp", "abs", "round", "floor", "ceil"
    )
    
    // State for persistent variables across executions
    private val state = mutableMapOf<String, Any>()
    
    /**
     * Execute a safe expression.
     */
    fun execute(code: String): String {
        return try {
            // Parse and validate the expression
            val sanitized = sanitize(code)
            val result = evaluate(sanitized)
            result.toString()
        } catch (e: Exception) {
            throw REPLError("Execution error: ${e.message}")
        }
    }
    
    /**
     * Execute a batch of expressions.
     */
    fun executeBatch(codes: List<String>): List<String> {
        return codes.map { execute(it) }
    }
    
    /**
     * Set a variable in state.
     */
    fun setVariable(name: String, value: Any) {
        state[name] = value
    }
    
    /**
     * Get a variable from state.
     */
    fun getVariable(name: String): Any? = state[name]
    
    /**
     * Clear all state.
     */
    fun clearState() {
        state.clear()
    }
    
    private fun sanitize(code: String): String {
        // Remove potentially dangerous patterns
        return code
            .replace(Regex("import\\s+"), "")
            .replace(Regex("exec\\s*\\("), "")
            .replace(Regex("eval\\s*\\("), "")
            .replace(Regex("__\\w+__"), "")
            .trim()
    }
    
    private fun evaluate(expr: String): Any {
        // Simple expression evaluator
        // For production, use a proper expression parser
        return try {
            // Try numeric evaluation
            evaluateMathExpression(expr)
        } catch (e: Exception) {
            // Return as string
            expr
        }
    }
    
    private fun evaluateMathExpression(expr: String): Double {
        var expression = expr.trim().lowercase()
        
        // Replace common math functions and constants
        val replacements = mapOf(
            "pi" to Math.PI.toString(),
            "e" to Math.E.toString(),
            "sqrt" to "Math.sqrt",
            "sin" to "Math.sin",
            "cos" to "Math.cos",
            "tan" to "Math.tan",
            "log" to "Math.log",
            "exp" to "Math.exp",
            "abs" to "Math.abs"
        )
        
        for ((old, new) in replacements) {
            expression = expression.replace(old, new)
        }
        
        // Simple expression parser for basic math
        return parseExpression(expression)
    }
    
    private fun parseExpression(expr: String): Double {
        var s = expr.replace(" ", "")
        return parseAddSub(s)
    }
    
    private fun parseAddSub(expr: String): Double {
        var result = 0.0
        var current = ""
        var op = '+'
        
        var i = 0
        while (i < expr.length) {
            val c = expr[i]
            when {
                c == '+' || c == '-' -> {
                    result = when (op) {
                        '+' -> result + parseMulDiv(current)
                        '-' -> result - parseMulDiv(current)
                        else -> result
                    }
                    current = ""
                    op = c
                }
                else -> current += c
            }
            i++
        }
        
        return when (op) {
            '+' -> result + parseMulDiv(current)
            '-' -> result - parseMulDiv(current)
            else -> result
        }
    }
    
    private fun parseMulDiv(expr: String): Double {
        var result = 1.0
        var current = ""
        var op = '*'
        var first = true
        
        var i = 0
        while (i < expr.length) {
            val c = expr[i]
            when {
                c == '*' || c == '/' -> {
                    result = if (first) {
                        first = false
                        current.toDoubleOrNull() ?: 0.0
                    } else when (op) {
                        '*' -> result * (current.toDoubleOrNull() ?: 1.0)
                        '/' -> result / (current.toDoubleOrNull() ?: 1.0)
                        else -> result
                    }
                    current = ""
                    op = c
                }
                else -> current += c
            }
            i++
        }
        
        return if (first) {
            current.toDoubleOrNull() ?: 0.0
        } else when (op) {
            '*' -> result * (current.toDoubleOrNull() ?: 1.0)
            '/' -> result / (current.toDoubleOrNull() ?: 1.0)
            else -> result
        }
    }
}

// ========== Parser (from parser.py) ==========

/**
 * Parsed response from the LLM.
 */
data class ParsedResponse(
    val thinking: String? = null,
    val answer: String? = null,
    val code: String? = null,
    val toolCalls: List<ToolCall> = emptyList(),
    val isRecursive: Boolean = false,
    val isFinal: Boolean = false
)

/**
 * Parse an LLM response to extract structured components.
 */
fun parseResponse(response: String): ParsedResponse {
    var thinking: String? = null
    var answer: String? = null
    var code: String? = null
    val toolCalls = mutableListOf<ToolCall>()
    
    // Extract thinking block
    val thinkingMatch = Regex("<thinking>(.*?)</thinking>", RegexOption.DOT_MATCHES_ALL)
        .find(response)
    thinking = thinkingMatch?.groupValues?.get(1)?.trim()
    
    // Extract answer block
    val answerMatch = Regex("<answer>(.*?)</answer>", RegexOption.DOT_MATCHES_ALL)
        .find(response)
    answer = answerMatch?.groupValues?.get(1)?.trim()
    
    // Extract code block
    val codeMatch = Regex("<code>(.*?)</code>", RegexOption.DOT_MATCHES_ALL)
        .find(response)
    code = codeMatch?.groupValues?.get(1)?.trim()
    
    // Extract tool calls
    val toolPattern = Regex("<tool_call>\\s*name:\\s*(\\w+)\\s*args:\\s*\\{([^}]*)\\}\\s*</tool_call>")
    toolPattern.findAll(response).forEach { match ->
        val name = match.groupValues[1]
        val argsStr = match.groupValues[2]
        val args = mutableMapOf<String, String>()
        
        Regex("(\\w+):\\s*\"([^\"]*)\"").findAll(argsStr).forEach { argMatch ->
            args[argMatch.groupValues[1]] = argMatch.groupValues[2]
        }
        
        toolCalls.add(ToolCall(
            id = java.util.UUID.randomUUID().toString(),
            name = name,
            arguments = args
        ))
    }
    
    // Check if final (has answer and no pending operations)
    val isFinal = answer != null && code == null && toolCalls.isEmpty()
    val isRecursive = code != null || toolCalls.isNotEmpty()
    
    return ParsedResponse(
        thinking = thinking,
        answer = answer,
        code = code,
        toolCalls = toolCalls,
        isRecursive = isRecursive,
        isFinal = isFinal
    )
}

/**
 * Check if a response is final (no more iterations needed).
 */
fun isFinal(response: String): Boolean {
    val hasAnswer = response.contains("<answer>") && response.contains("</answer>")
    val hasCode = response.contains("<code>")
    val hasToolCall = response.contains("<tool_call>")
    return hasAnswer && !hasCode && !hasToolCall
}

// ========== Prompts (from prompts.py) ==========

/**
 * Build the system prompt for RLM.
 */
fun buildSystemPrompt(
    personality: String = "",
    tools: List<ToolDefinition> = emptyList(),
    userName: String = "User"
): String {
    val toolsSection = if (tools.isNotEmpty()) {
        val toolDescriptions = tools.joinToString("\n") { tool ->
            """
            - ${tool.name}: ${tool.description}
              Parameters: ${tool.parameters.entries.joinToString(", ") { "${it.key}: ${it.value.type}" }}
            """.trimIndent()
        }
        """
        
        ## Available Tools
        You have access to the following tools:
        $toolDescriptions
        
        To use a tool, format your response as:
        <tool_call>
        name: tool_name
        args: {"param1": "value1", "param2": "value2"}
        </tool_call>
        """.trimIndent()
    } else ""
    
    return """
    You are an AI assistant in a chat room. $personality
    
    You can think step-by-step using <thinking></thinking> tags.
    When you have a final answer, wrap it in <answer></answer> tags.
    
    If you need to execute code or calculations, use <code></code> tags.
    $toolsSection
    
    Current user: $userName
    
    Remember to be helpful, accurate, and respectful.
    """.trimIndent()
}

/**
 * Build a RAG-enhanced system prompt.
 */
fun buildRAGSystemPrompt(
    personality: String = "",
    context: String,
    tools: List<ToolDefinition> = emptyList(),
    userName: String = "User"
): String {
    val basePrompt = buildSystemPrompt(personality, tools, userName)
    
    return """
    $basePrompt
    
    ## Relevant Context
    The following information may be relevant to the conversation:
    
    $context
    
    Use this context to inform your responses when relevant, but don't force it if not applicable.
    """.trimIndent()
}

// ========== RLM Core (from core.py) ==========

/**
 * RLM Error base class.
 */
open class RLMError(message: String) : Exception(message)

/**
 * Max iterations exceeded error.
 */
class MaxIterationsError(message: String) : RLMError(message)

/**
 * Max recursion depth exceeded error.
 */
class MaxDepthError(message: String) : RLMError(message)

/**
 * LLM Provider interface.
 */
interface LLMProvider {
    suspend fun complete(messages: List<RLMMessage>, temperature: Float = 0.7f): String
}

/**
 * Ollama API DTOs and Interface
 */
data class OllamaChatRequest(
    val model: String,
    val messages: List<OllamaMessage>,
    val stream: Boolean = false,
    val options: OllamaOptions? = null
)

data class OllamaMessage(
    val role: String,
    val content: String,
    val images: List<String>? = null
)

data class OllamaOptions(
    val temperature: Float
)

data class OllamaChatResponse(
    val model: String,
    @SerializedName("created_at") val createdAt: String,
    val message: OllamaMessage,
    val done: Boolean,
    @SerializedName("total_duration") val totalDuration: Long? = null
)

interface OllamaApi {
    @POST("api/chat")
    fun chat(@Body request: OllamaChatRequest): Call<OllamaChatResponse>
}

/**
 * Ollama LLM Provider.
 */
class OllamaProvider(
    private val model: String,
    private val baseUrl: String = "http://localhost:11434",
    api: OllamaApi? = null
) : LLMProvider {

    @Volatile
    private var _api: OllamaApi? = api

    override suspend fun complete(messages: List<RLMMessage>, temperature: Float): String {
        return withContext(Dispatchers.IO) {
            val currentApi = _api ?: synchronized(this@OllamaProvider) {
                _api ?: Retrofit.Builder()
                    .baseUrl(if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/")
                    .addConverterFactory(GsonConverterFactory.create())
                    .build()
                    .create(OllamaApi::class.java).also { _api = it }
            }

            val ollamaMessages = messages.map { rlmMsg ->
                OllamaMessage(
                    role = rlmMsg.role,
                    content = rlmMsg.content
                )
            }

            val request = OllamaChatRequest(
                model = model,
                messages = ollamaMessages,
                stream = false,
                options = OllamaOptions(temperature = temperature)
            )

            try {
                val response = currentApi.chat(request).execute()
                if (response.isSuccessful) {
                    response.body()?.message?.content ?: throw RLMError("Empty response from Ollama")
                } else {
                    throw RLMError("Ollama API error: ${response.code()} ${response.errorBody()?.string()}")
                }
            } catch (e: Exception) {
                throw RLMError("Failed to connect to Ollama: ${e.message}")
            }
        }
    }
}

/**
 * Recursive Language Model.
 */
class RLM(
    private val model: String,
    private val recursiveModel: String? = null,
    private val apiBase: String? = null,
    private val apiKey: String? = null,
    private val maxDepth: Int = 5,
    private val maxIterations: Int = 30,
    private val ragStore: AIRAGStore? = null,
    private val aiName: String = "AI",
    private val llmProvider: LLMProvider? = null
) {
    private var currentDepth = 0
    private val repl = REPLExecutor()
    
    // Stats
    private var llmCalls = 0
    private var iterations = 0
    
    /**
     * Sync wrapper for acompletion.
     */
    fun completion(
        query: String = "",
        context: String = "",
        tools: List<ToolDefinition> = emptyList(),
        temperature: Float = 0.7f
    ): String {
        return runBlocking {
            acompletion(query, context, tools, temperature)
        }
    }
    
    /**
     * Main async completion method.
     */
    suspend fun acompletion(
        query: String = "",
        context: String = "",
        tools: List<ToolDefinition> = emptyList(),
        temperature: Float = 0.7f
    ): String {
        if (currentDepth >= maxDepth) {
            throw MaxDepthError("Max recursion depth ($maxDepth) exceeded")
        }
        
        // Build messages
        val messages = mutableListOf<RLMMessage>()
        
        // System prompt with optional RAG context
        val systemPrompt = if (ragStore != null && context.isNotEmpty()) {
            // Get relevant context from RAG
            val ragResults = ragStore.retrieve(context, topK = 5)
            val ragContext = ragResults.joinToString("\n\n") { it.chunk.content }
            buildRAGSystemPrompt(aiName, ragContext, tools)
        } else {
            buildSystemPrompt(aiName, tools)
        }
        
        messages.add(RLMMessage(role = MessageRole.SYSTEM.value, content = systemPrompt))
        
        // Add user query
        val userContent = if (context.isNotEmpty() && query.isNotEmpty()) {
            "$query\n\nContext:\n$context"
        } else {
            query.ifEmpty { context }
        }
        messages.add(RLMMessage(role = MessageRole.USER.value, content = userContent))
        
        // Main iteration loop
        var iterationCount = 0
        
        while (iterationCount < maxIterations) {
            iterationCount++
            iterations++
            
            // Call LLM
            val response = callLLM(messages, temperature)
            llmCalls++
            
            // Parse response
            val parsed = parseResponse(response)
            
            // Add assistant response to messages
            messages.add(RLMMessage(role = MessageRole.ASSISTANT.value, content = response))
            
            // If final, return answer
            if (parsed.isFinal && parsed.answer != null) {
                return parsed.answer
            }
            
            // Execute code if present
            if (parsed.code != null) {
                val codeResult = try {
                    repl.execute(parsed.code)
                } catch (e: REPLError) {
                    "Error: ${e.message}"
                }
                
                messages.add(RLMMessage(
                    role = MessageRole.TOOL.value,
                    content = "Code execution result: $codeResult"
                ))
            }
            
            // Execute tool calls
            for (toolCall in parsed.toolCalls) {
                val toolResult = executeToolCall(toolCall, tools)
                messages.add(RLMMessage(
                    role = MessageRole.TOOL.value,
                    content = "Tool ${toolCall.name} result: ${toolResult.result}",
                    toolCallId = toolCall.id
                ))
            }
            
            // Handle recursion
            if (parsed.isRecursive && currentDepth < maxDepth - 1) {
                // Create nested RLM for recursion
                val nestedRlm = RLM(
                    model = recursiveModel ?: model,
                    maxDepth = maxDepth,
                    maxIterations = maxIterations - iterationCount,
                    ragStore = ragStore,
                    aiName = aiName,
                    llmProvider = llmProvider
                )
                nestedRlm.currentDepth = currentDepth + 1
            }
        }
        
        throw MaxIterationsError("Max iterations ($maxIterations) exceeded")
    }
    
    /**
     * Get execution stats.
     */
    fun getStats(): Map<String, Int> = mapOf(
        "llm_calls" to llmCalls,
        "iterations" to iterations
    )
    
    /**
     * Reset stats.
     */
    fun resetStats() {
        llmCalls = 0
        iterations = 0
    }
    
    private suspend fun callLLM(messages: List<RLMMessage>, temperature: Float): String {
        return if (llmProvider != null) {
            llmProvider.complete(messages, temperature)
        } else {
            // Default Ollama provider
            val provider = OllamaProvider(model, apiBase ?: "http://localhost:11434")
            provider.complete(messages, temperature)
        }
    }
    
    private fun executeToolCall(
        toolCall: ToolCall,
        tools: List<ToolDefinition>
    ): ToolCallResult {
        val tool = tools.find { it.name == toolCall.name }
            ?: return ToolCallResult(
                id = toolCall.id,
                name = toolCall.name,
                result = "Error: Tool '${toolCall.name}' not found",
                success = false
            )
        
        return try {
            // Convert String arguments to Any? for tool execution
            // Tool parameters are stored as strings in ToolCall but tools expect Map<String, Any?>
            val typedArguments: Map<String, Any?> = toolCall.arguments.mapValues { (key, value) ->
                // Attempt to parse the string value to appropriate type
                when {
                    value.equals("true", ignoreCase = true) -> true
                    value.equals("false", ignoreCase = true) -> false
                    value.toDoubleOrNull() != null -> value.toDouble()
                    value.toIntOrNull() != null -> value.toInt()
                    else -> value  // Keep as string
                }
            }
            
            val result = tool.execute(typedArguments)
            ToolCallResult(
                id = toolCall.id,
                name = toolCall.name,
                result = result.output ?: result.error ?: "No result",
                success = result.success
            )
        } catch (e: Exception) {
            ToolCallResult(
                id = toolCall.id,
                name = toolCall.name,
                result = "Error: ${e.message}",
                success = false
            )
        }
    }
}

/**
 * Create an RLM instance with default configuration.
 */
fun createRLM(
    model: String = "gemma3:4b",
    aiName: String = "AI",
    ragStore: AIRAGStore? = null,
    ollamaUrl: String = "http://localhost:11434"
): RLM {
    return RLM(
        model = model,
        apiBase = ollamaUrl,
        ragStore = ragStore,
        aiName = aiName,
        llmProvider = OllamaProvider(model, ollamaUrl)
    )
}
