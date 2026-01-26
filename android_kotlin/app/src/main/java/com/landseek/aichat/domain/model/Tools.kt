/**
 * AI Tools Module - Function calling capabilities for AI Chat Room
 *
 * This module provides a collection of tools that AI participants can use
 * to perform various actions like calculations, web searches, file operations,
 * date/time queries, and more.
 *
 * Tools are designed to be safe and run locally on Pixel 10 Pro.
 * 
 * Converted from Python: src/tools.py
 */

package com.landseek.aichat.domain.model

import kotlinx.serialization.Serializable
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.time.temporal.ChronoUnit
import kotlin.math.*

/**
 * Result from a tool execution.
 */
@Serializable
data class ToolResult(
    val success: Boolean,
    val output: String?,
    val error: String? = null
) {
    override fun toString(): String {
        return if (success) {
            "✅ $output"
        } else {
            "❌ Error: $error"
        }
    }
}

/**
 * Parameter definition for a tool.
 */
@Serializable
data class ToolParameter(
    val type: String,
    val description: String,
    val required: Boolean = false
)

/**
 * Represents a callable tool for AI agents.
 */
data class Tool(
    val name: String,
    val description: String,
    val parameters: Map<String, ToolParameter>,
    val function: (Map<String, Any?>) -> ToolResult,
    val category: String = "general"
) {
    /**
     * Convert to ToolDefinition for use with RLM/Addons.
     */
    fun toToolDefinition(): ToolDefinition = ToolDefinition(
        name = name,
        description = description,
        parameters = parameters,
        execute = function,
        category = category
    )
    /**
     * Convert tool to OpenAI-compatible function schema.
     */
    fun toSchema(): Map<String, Any> = mapOf(
        "type" to "function",
        "function" to mapOf(
            "name" to name,
            "description" to description,
            "parameters" to mapOf(
                "type" to "object",
                "properties" to parameters.mapValues { (_, param) ->
                    mapOf(
                        "type" to param.type,
                        "description" to param.description
                    )
                },
                "required" to parameters.filter { it.value.required }.keys.toList()
            )
        )
    )

    /**
     * Execute the tool with given arguments.
     */
    fun execute(kwargs: Map<String, Any?>): ToolResult {
        return try {
            function(kwargs)
        } catch (e: Exception) {
            ToolResult(success = false, output = null, error = e.message)
        }
    }
}

/**
 * Tool definition for use with RLM and Add-ons.
 *
 * This is the primary interface used by RLM.kt and Addons.kt for tool definitions.
 * Unlike Tool, this uses 'execute' as the function property name for clarity.
 */
data class ToolDefinition(
    val name: String,
    val description: String,
    val parameters: Map<String, ToolParameter>,
    val execute: (Map<String, Any?>) -> ToolResult,
    val category: String = "general"
) {
    /**
     * Convert to Tool for use with ToolRegistry.
     */
    fun toTool(): Tool = Tool(
        name = name,
        description = description,
        parameters = parameters,
        function = execute,
        category = category
    )
}

/**
 * Definition for an AI personality (used by Add-ons).
 */
data class PersonalityDefinition(
    val id: String,
    val name: String,
    val description: String,
    val systemPrompt: String,
    val traits: List<String> = emptyList(),
    val temperature: Float = 0.7f,
    val icon: String? = null
)

/**
 * Registry for managing available tools.
 */
class ToolRegistry {
    private val tools: MutableMap<String, Tool> = mutableMapOf()

    init {
        registerBuiltinTools()
    }

    /**
     * Register a tool.
     */
    fun register(tool: Tool) {
        tools[tool.name] = tool
    }

    /**
     * Get a tool by name.
     */
    fun get(name: String): Tool? = tools[name]

    /**
     * List all tools, optionally filtered by category.
     */
    fun listTools(category: String? = null): List<Tool> {
        val toolList = tools.values.toList()
        return if (category != null) {
            toolList.filter { it.category == category }
        } else {
            toolList
        }
    }

    /**
     * Get OpenAI-compatible schemas for all tools.
     */
    fun getSchemas(): List<Map<String, Any>> = tools.values.map { it.toSchema() }

    /**
     * Execute a tool by name.
     */
    fun execute(name: String, kwargs: Map<String, Any?>): ToolResult {
        val tool = get(name)
        return tool?.execute(kwargs) ?: ToolResult(
            success = false,
            output = null,
            error = "Tool '$name' not found"
        )
    }

    private fun registerBuiltinTools() {
        // Math tools
        register(Tool(
            name = "calculate",
            description = "Evaluate a mathematical expression. Supports basic arithmetic, " +
                    "trigonometry, logarithms, and common math functions.",
            parameters = mapOf(
                "expression" to ToolParameter(
                    type = "string",
                    description = "Mathematical expression to evaluate (e.g., '2 + 2', 'sin(3.14159/2)', 'sqrt(16)')",
                    required = true
                )
            ),
            function = ::calculate,
            category = "math"
        ))

        register(Tool(
            name = "unit_convert",
            description = "Convert between units of measurement.",
            parameters = mapOf(
                "value" to ToolParameter(
                    type = "number",
                    description = "The value to convert",
                    required = true
                ),
                "from_unit" to ToolParameter(
                    type = "string",
                    description = "Source unit (e.g., 'km', 'miles', 'celsius', 'fahrenheit')",
                    required = true
                ),
                "to_unit" to ToolParameter(
                    type = "string",
                    description = "Target unit",
                    required = true
                )
            ),
            function = ::unitConvert,
            category = "math"
        ))

        // Date/Time tools
        register(Tool(
            name = "get_current_time",
            description = "Get the current date and time.",
            parameters = mapOf(
                "format" to ToolParameter(
                    type = "string",
                    description = "Output format (e.g., 'iso', 'human', 'date', 'time')",
                    required = false
                )
            ),
            function = ::getCurrentTime,
            category = "datetime"
        ))

        register(Tool(
            name = "calculate_date",
            description = "Calculate a date by adding or subtracting days from a date.",
            parameters = mapOf(
                "base_date" to ToolParameter(
                    type = "string",
                    description = "Base date in YYYY-MM-DD format. Use 'today' for current date.",
                    required = true
                ),
                "days" to ToolParameter(
                    type = "integer",
                    description = "Number of days to add (negative to subtract)",
                    required = false
                ),
                "weeks" to ToolParameter(
                    type = "integer",
                    description = "Number of weeks to add (negative to subtract)",
                    required = false
                )
            ),
            function = ::calculateDate,
            category = "datetime"
        ))

        // Text tools
        register(Tool(
            name = "word_count",
            description = "Count words, characters, sentences, and paragraphs in text.",
            parameters = mapOf(
                "text" to ToolParameter(
                    type = "string",
                    description = "Text to analyze",
                    required = true
                )
            ),
            function = ::wordCount,
            category = "text"
        ))

        register(Tool(
            name = "search_text",
            description = "Search for a pattern in text using regular expressions.",
            parameters = mapOf(
                "text" to ToolParameter(
                    type = "string",
                    description = "Text to search in",
                    required = true
                ),
                "pattern" to ToolParameter(
                    type = "string",
                    description = "Regular expression pattern to search for",
                    required = true
                ),
                "case_sensitive" to ToolParameter(
                    type = "boolean",
                    description = "Whether search is case sensitive (default: false)",
                    required = false
                )
            ),
            function = ::searchText,
            category = "text"
        ))

        register(Tool(
            name = "extract_urls",
            description = "Extract all URLs from text.",
            parameters = mapOf(
                "text" to ToolParameter(
                    type = "string",
                    description = "Text to extract URLs from",
                    required = true
                )
            ),
            function = ::extractUrls,
            category = "text"
        ))

        register(Tool(
            name = "extract_emails",
            description = "Extract all email addresses from text.",
            parameters = mapOf(
                "text" to ToolParameter(
                    type = "string",
                    description = "Text to extract emails from",
                    required = true
                )
            ),
            function = ::extractEmails,
            category = "text"
        ))

        // System tools
        register(Tool(
            name = "get_system_info",
            description = "Get system information (OS, Java version, etc.).",
            parameters = emptyMap(),
            function = ::getSystemInfo,
            category = "system"
        ))
    }
}

// Tool implementations

/** Maximum length for mathematical expressions */
private const val MAX_EXPRESSION_LENGTH = 200

/** Allowed mathematical function names */
private val ALLOWED_MATH_FUNCTIONS = setOf(
    "sqrt", "sin", "cos", "tan", "asin", "acos", "atan",
    "log", "log10", "log2", "exp", "abs", "floor", "ceil",
    "round", "min", "max", "pow", "pi", "e", "tau"
)

/**
 * Evaluate a mathematical expression safely.
 */
fun calculate(kwargs: Map<String, Any?>): ToolResult {
    val expression = kwargs["expression"] as? String
        ?: return ToolResult(success = false, output = null, error = "Expression required")

    // Validate expression - only allow safe characters (digits, operators, parentheses, dots, spaces)
    // Letters are only allowed as part of known function names
    val allowedCharsPattern = Regex("^[\\d\\s+\\-*/().]+$")
    val withoutFunctions = ALLOWED_MATH_FUNCTIONS.fold(expression.lowercase()) { acc, func ->
        acc.replace(func, "")
    }
    
    // After removing known functions, only operators and numbers should remain
    if (!withoutFunctions.matches(allowedCharsPattern)) {
        return ToolResult(success = false, output = null, error = "Expression contains invalid characters or unknown functions")
    }

    // Limit expression length to prevent DoS
    if (expression.length > MAX_EXPRESSION_LENGTH) {
        return ToolResult(success = false, output = null, error = "Expression too long (max $MAX_EXPRESSION_LENGTH characters)")
    }

    return try {
        // Simple expression evaluator for basic math
        val result = evaluateExpression(expression)
        ToolResult(success = true, output = result.toString())
    } catch (e: Exception) {
        ToolResult(success = false, output = null, error = e.message)
    }
}

/**
 * Simple expression evaluator supporting basic operations and common math functions.
 */
private fun evaluateExpression(expr: String): Double {
    var expression = expr.trim().lowercase()

    // Replace common math functions and constants
    val replacements = mapOf(
        "pi" to Math.PI.toString(),
        "e" to Math.E.toString(),
        "sqrt" to "√",
        "sin" to "SIN",
        "cos" to "COS",
        "tan" to "TAN",
        "log" to "LOG",
        "abs" to "ABS"
    )
    
    replacements.forEach { (key, value) ->
        expression = expression.replace(key, value)
    }

    // Handle function calls (simplified)
    val funcPattern = Regex("(√|SIN|COS|TAN|LOG|ABS)\\(([^)]+)\\)")
    while (funcPattern.containsMatchIn(expression)) {
        expression = funcPattern.replace(expression) { match ->
            val func = match.groupValues[1]
            val arg = evaluateExpression(match.groupValues[2])
            when (func) {
                "√" -> sqrt(arg).toString()
                "SIN" -> sin(arg).toString()
                "COS" -> cos(arg).toString()
                "TAN" -> tan(arg).toString()
                "LOG" -> ln(arg).toString()
                "ABS" -> abs(arg).toString()
                else -> throw IllegalArgumentException("Unknown function: $func")
            }
        }
    }

    // Evaluate basic arithmetic
    return evaluateArithmetic(expression)
}

/**
 * Evaluate basic arithmetic expression.
 */
private fun evaluateArithmetic(expr: String): Double {
    var expression = expr.replace(" ", "")
    
    // Handle parentheses recursively
    val parenPattern = Regex("\\(([^()]+)\\)")
    while (parenPattern.containsMatchIn(expression)) {
        expression = parenPattern.replace(expression) { match ->
            evaluateArithmetic(match.groupValues[1]).toString()
        }
    }

    // Tokenize
    val tokens = mutableListOf<Any>()
    var currentNumber = StringBuilder()
    var i = 0
    while (i < expression.length) {
        val c = expression[i]
        when {
            c.isDigit() || c == '.' -> currentNumber.append(c)
            c == '-' && (tokens.isEmpty() || tokens.last() is Char) -> currentNumber.append(c)
            c in "+-*/" -> {
                if (currentNumber.isNotEmpty()) {
                    tokens.add(currentNumber.toString().toDouble())
                    currentNumber = StringBuilder()
                }
                tokens.add(c)
            }
        }
        i++
    }
    if (currentNumber.isNotEmpty()) {
        tokens.add(currentNumber.toString().toDouble())
    }

    // Evaluate * and / first
    var j = 0
    while (j < tokens.size) {
        if (tokens[j] is Char && (tokens[j] == '*' || tokens[j] == '/')) {
            val left = tokens[j - 1] as Double
            val right = tokens[j + 1] as Double
            val result = if (tokens[j] == '*') left * right else left / right
            tokens[j - 1] = result
            tokens.removeAt(j)
            tokens.removeAt(j)
            j--
        }
        j++
    }

    // Evaluate + and -
    var result = tokens.firstOrNull() as? Double ?: 0.0
    var k = 1
    while (k < tokens.size) {
        val op = tokens[k] as Char
        val right = tokens[k + 1] as Double
        result = if (op == '+') result + right else result - right
        k += 2
    }

    return result
}

/**
 * Convert between units.
 */
fun unitConvert(kwargs: Map<String, Any?>): ToolResult {
    val value = (kwargs["value"] as? Number)?.toDouble()
        ?: return ToolResult(success = false, output = null, error = "Value required")
    val fromUnit = (kwargs["from_unit"] as? String)?.lowercase()
        ?: return ToolResult(success = false, output = null, error = "from_unit required")
    val toUnit = (kwargs["to_unit"] as? String)?.lowercase()
        ?: return ToolResult(success = false, output = null, error = "to_unit required")

    val conversions = mapOf<Pair<String, String>, (Double) -> Double>(
        // Length
        Pair("km", "miles") to { x -> x * 0.621371 },
        Pair("miles", "km") to { x -> x * 1.60934 },
        Pair("m", "ft") to { x -> x * 3.28084 },
        Pair("ft", "m") to { x -> x * 0.3048 },
        Pair("cm", "inches") to { x -> x * 0.393701 },
        Pair("inches", "cm") to { x -> x * 2.54 },

        // Temperature
        Pair("celsius", "fahrenheit") to { x -> x * 9 / 5 + 32 },
        Pair("fahrenheit", "celsius") to { x -> (x - 32) * 5 / 9 },
        Pair("celsius", "kelvin") to { x -> x + 273.15 },
        Pair("kelvin", "celsius") to { x -> x - 273.15 },

        // Weight
        Pair("kg", "lbs") to { x -> x * 2.20462 },
        Pair("lbs", "kg") to { x -> x * 0.453592 },
        Pair("g", "oz") to { x -> x * 0.035274 },
        Pair("oz", "g") to { x -> x * 28.3495 },

        // Volume
        Pair("liters", "gallons") to { x -> x * 0.264172 },
        Pair("gallons", "liters") to { x -> x * 3.78541 },
        Pair("ml", "fl_oz") to { x -> x * 0.033814 },
        Pair("fl_oz", "ml") to { x -> x * 29.5735 }
    )

    val key = Pair(fromUnit, toUnit)
    val conversion = conversions[key]
        ?: return ToolResult(success = false, output = null, error = "Unknown conversion: $fromUnit to $toUnit")

    val result = conversion(value)
    return ToolResult(success = true, output = "$value $fromUnit = ${"%.4f".format(result)} $toUnit")
}

/**
 * Get current date and time.
 */
fun getCurrentTime(kwargs: Map<String, Any?>): ToolResult {
    val format = kwargs["format"] as? String ?: "human"
    val now = LocalDateTime.now()

    val output = when (format) {
        "iso" -> now.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
        "date" -> now.format(DateTimeFormatter.ISO_LOCAL_DATE)
        "time" -> now.format(DateTimeFormatter.ofPattern("HH:mm:ss"))
        else -> now.format(DateTimeFormatter.ofPattern("EEEE, MMMM dd, yyyy 'at' hh:mm a"))
    }

    return ToolResult(success = true, output = output)
}

/**
 * Calculate a date from base date.
 */
fun calculateDate(kwargs: Map<String, Any?>): ToolResult {
    val baseDate = kwargs["base_date"] as? String
        ?: return ToolResult(success = false, output = null, error = "base_date required")
    val days = (kwargs["days"] as? Number)?.toLong() ?: 0L
    val weeks = (kwargs["weeks"] as? Number)?.toLong() ?: 0L

    return try {
        val base = if (baseDate.lowercase() == "today") {
            LocalDate.now()
        } else {
            LocalDate.parse(baseDate)
        }

        val totalDays = days + (weeks * 7)
        val result = base.plusDays(totalDays)

        val formatted = result.format(DateTimeFormatter.ofPattern("EEEE, MMMM dd, yyyy"))
        ToolResult(success = true, output = "${result.format(DateTimeFormatter.ISO_LOCAL_DATE)} ($formatted)")
    } catch (e: Exception) {
        ToolResult(success = false, output = null, error = e.message)
    }
}

/**
 * Count words, characters, etc. in text.
 */
fun wordCount(kwargs: Map<String, Any?>): ToolResult {
    val text = kwargs["text"] as? String
        ?: return ToolResult(success = false, output = null, error = "text required")

    val words = text.split(Regex("\\s+")).filter { it.isNotEmpty() }.size
    val chars = text.length
    val charsNoSpaces = text.replace(" ", "").length
    val sentences = Regex("[.!?]+").findAll(text).count()
    val paragraphs = text.split(Regex("\n\n+")).filter { it.trim().isNotEmpty() }.size
    val lines = text.split("\n").size

    val output = """
        |Words: $words
        |Characters: $chars
        |Characters (no spaces): $charsNoSpaces
        |Sentences: $sentences
        |Paragraphs: $paragraphs
        |Lines: $lines
    """.trimMargin()

    return ToolResult(success = true, output = output)
}

/**
 * Search for pattern in text.
 */
fun searchText(kwargs: Map<String, Any?>): ToolResult {
    val text = kwargs["text"] as? String
        ?: return ToolResult(success = false, output = null, error = "text required")
    val pattern = kwargs["pattern"] as? String
        ?: return ToolResult(success = false, output = null, error = "pattern required")
    val caseSensitive = kwargs["case_sensitive"] as? Boolean ?: false

    return try {
        val options = if (caseSensitive) emptySet() else setOf(RegexOption.IGNORE_CASE)
        val regex = Regex(pattern, options)
        val matches = regex.findAll(text).map { it.value }.toList()

        val output = """
            |Matches: ${matches.joinToString(", ")}
            |Count: ${matches.size}
        """.trimMargin()

        ToolResult(success = true, output = output)
    } catch (e: Exception) {
        ToolResult(success = false, output = null, error = e.message)
    }
}

/**
 * Extract URLs from text.
 */
fun extractUrls(kwargs: Map<String, Any?>): ToolResult {
    val text = kwargs["text"] as? String
        ?: return ToolResult(success = false, output = null, error = "text required")

    val urlPattern = Regex("https?://[^\\s<>\"{}|\\\\^`\\[\\]]+")
    val urls = urlPattern.findAll(text).map { it.value }.toList()

    val output = """
        |URLs: ${urls.joinToString(", ")}
        |Count: ${urls.size}
    """.trimMargin()

    return ToolResult(success = true, output = output)
}

/**
 * Extract email addresses from text.
 */
fun extractEmails(kwargs: Map<String, Any?>): ToolResult {
    val text = kwargs["text"] as? String
        ?: return ToolResult(success = false, output = null, error = "text required")

    val emailPattern = Regex("[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}")
    val emails = emailPattern.findAll(text).map { it.value }.toList()

    val output = """
        |Emails: ${emails.joinToString(", ")}
        |Count: ${emails.size}
    """.trimMargin()

    return ToolResult(success = true, output = output)
}

/**
 * Get system information.
 */
fun getSystemInfo(kwargs: Map<String, Any?>): ToolResult {
    val info = """
        |OS: ${System.getProperty("os.name")}
        |OS Version: ${System.getProperty("os.version")}
        |Java Version: ${System.getProperty("java.version")}
        |Architecture: ${System.getProperty("os.arch")}
        |User: ${System.getProperty("user.name")}
    """.trimMargin()

    return ToolResult(success = true, output = info)
}

/**
 * Global tool registry instance
 */
val toolRegistry = ToolRegistry()

/**
 * Get a formatted description of all available tools.
 */
fun getToolsDescription(): String {
    val categories = mutableMapOf<String, MutableList<Tool>>()
    
    for (tool in toolRegistry.listTools()) {
        if (tool.category !in categories) {
            categories[tool.category] = mutableListOf()
        }
        categories[tool.category]?.add(tool)
    }

    val lines = mutableListOf("Available Tools:\n")
    for ((category, tools) in categories.toSortedMap()) {
        lines.add("\n📁 ${category.uppercase()}")
        for (tool in tools) {
            val params = tool.parameters.keys.joinToString(", ").ifEmpty { "none" }
            val desc = tool.description.take(60) + if (tool.description.length > 60) "..." else ""
            lines.add("  • ${tool.name}($params): $desc")
        }
    }

    return lines.joinToString("\n")
}

/**
 * Parse a tool call from AI response text.
 *
 * Expected format: @tool_name(arg1=value1, arg2=value2)
 * Or: @tool_name{"arg1": "value1", "arg2": "value2"}
 */
fun parseToolCall(text: String): Map<String, Any>? {
    val pattern = Regex("@(\\w+)(?:\\(([^)]*)\\)|\\{([^}]+)\\})")
    val match = pattern.find(text) ?: return null

    val toolName = match.groupValues[1]

    // Try parentheses format first
    if (match.groupValues[2].isNotEmpty()) {
        val argsStr = match.groupValues[2]
        val kwargs = mutableMapOf<String, Any>()
        
        if (argsStr.trim().isNotEmpty()) {
            // Parse key=value pairs
            for (pair in argsStr.split(",")) {
                val parts = pair.split("=", limit = 2)
                if (parts.size == 2) {
                    val key = parts[0].trim()
                    var value: Any = parts[1].trim().trim('"', '\'')
                    
                    // Try to convert to appropriate type
                    value = when {
                        value.toString().lowercase() == "true" -> true
                        value.toString().lowercase() == "false" -> false
                        value.toString().matches(Regex("-?\\d+")) -> value.toString().toInt()
                        value.toString().matches(Regex("-?\\d+\\.?\\d*")) -> value.toString().toDouble()
                        else -> value
                    }
                    kwargs[key] = value
                }
            }
        }
        return mapOf("tool" to toolName, "arguments" to kwargs)
    }

    return mapOf("tool" to toolName, "arguments" to emptyMap<String, Any>())
}
