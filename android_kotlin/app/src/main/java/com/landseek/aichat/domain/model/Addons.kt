/**
 * Add-on System for AI Chat Room
 *
 * This module provides a plugin/add-on architecture that allows extending
 * the AI Chat Room with custom functionality. Add-ons can provide:
 * - Custom tools for AI participants
 * - Custom AI personalities
 * - UI extensions
 * - Integration with external services
 *
 * Converted from Python: src/addons/__init__.py
 */

package com.landseek.aichat.domain.model

import android.content.Context
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.File
import java.time.Instant

/**
 * Metadata for an add-on.
 */
@Serializable
data class AddonMetadata(
    val id: String,
    val name: String,
    val version: String,
    val description: String,
    val author: String,
    val homepage: String? = null,
    val dependencies: List<String> = emptyList(),
    val minAppVersion: String = "0.1.0",
    val permissions: List<String> = emptyList(),
    var enabled: Boolean = true
)

/**
 * Result of loading an add-on.
 */
sealed class AddonLoadResult {
    data class Success(val addon: Addon) : AddonLoadResult()
    data class Error(val message: String) : AddonLoadResult()
}

/**
 * Interface for add-on hooks.
 */
interface AddonHooks {
    fun onMessage(sender: String, content: String): String? = null
    fun onAiResponse(aiName: String, response: String): String? = null
    fun onToolCall(toolName: String, args: Map<String, Any?>): Any? = null
    fun onDocumentUpload(document: DocumentContent): DocumentContent? = null
}

/**
 * Base class for add-ons.
 */
abstract class Addon(val metadata: AddonMetadata) : AddonHooks {
    var loaded = false
        private set
    
    /**
     * Called when the add-on is loaded.
     * Return true if successful.
     */
    abstract fun onLoad(): Boolean
    
    /**
     * Called when the add-on is unloaded.
     * Return true if successful.
     */
    abstract fun onUnload(): Boolean
    
    /**
     * Called when the add-on is enabled.
     */
    open fun onEnable(): Boolean = true
    
    /**
     * Called when the add-on is disabled.
     */
    open fun onDisable(): Boolean = true
    
    /**
     * Return list of tools provided by this add-on.
     */
    open fun getTools(): List<ToolDefinition> = emptyList()
    
    /**
     * Return list of AI personalities provided by this add-on.
     */
    open fun getPersonalities(): List<PersonalityDefinition> = emptyList()
    
    /**
     * Return dict of chat commands provided by this add-on.
     */
    open fun getCommands(): Map<String, (String) -> String> = emptyMap()
    
    internal fun markLoaded() { loaded = true }
    internal fun markUnloaded() { loaded = false }
}

/**
 * Example add-on implementation.
 */
class SampleAddon(metadata: AddonMetadata) : Addon(metadata) {
    override fun onLoad(): Boolean {
        println("Sample add-on loaded!")
        return true
    }
    
    override fun onUnload(): Boolean {
        println("Sample add-on unloaded!")
        return true
    }
    
    override fun getTools(): List<ToolDefinition> {
        return listOf(
            ToolDefinition(
                name = "sample_tool",
                description = "A sample tool from the add-on",
                parameters = mapOf(
                    "message" to ToolParameter(
                        type = "string",
                        description = "Message to echo",
                        required = true
                    )
                ),
                execute = { args ->
                    val message = args["message"] as? String ?: "No message"
                    ToolResult(success = true, output = "Echo: $message")
                }
            )
        )
    }
    
    override fun onMessage(sender: String, content: String): String? {
        // Example: transform messages
        return null
    }
}

/**
 * Add-on Manager - manages loading, unloading, and execution of add-ons.
 */
class AddonManager(private val addonsDir: String? = null) {
    private val addons = mutableMapOf<String, Addon>()
    private val metadataCache = mutableMapOf<String, AddonMetadata>()
    private val json = Json { ignoreUnknownKeys = true; prettyPrint = true }
    
    // Hook registrations
    private val messageHooks = mutableListOf<(String, String) -> String?>()
    private val aiResponseHooks = mutableListOf<(String, String) -> String?>()
    private val toolCallHooks = mutableListOf<(String, Map<String, Any?>) -> Any?>()
    private val documentUploadHooks = mutableListOf<(DocumentContent) -> DocumentContent?>()
    
    /**
     * Discover all available add-ons in the addons directory.
     */
    fun discoverAddons(): List<AddonMetadata> {
        val discovered = mutableListOf<AddonMetadata>()
        
        val dir = addonsDir?.let { File(it) } ?: return discovered
        if (!dir.exists()) {
            dir.mkdirs()
            return discovered
        }
        
        for (item in dir.listFiles() ?: emptyArray()) {
            if (item.isDirectory) {
                val manifestFile = File(item, "manifest.json")
                if (manifestFile.exists()) {
                    try {
                        val content = manifestFile.readText()
                        val metadata = json.decodeFromString<AddonMetadata>(content)
                        val metadataWithId = metadata.copy(id = item.name)
                        discovered.add(metadataWithId)
                        metadataCache[item.name] = metadataWithId
                    } catch (e: Exception) {
                        println("Error loading manifest for ${item.name}: ${e.message}")
                    }
                }
            }
        }
        
        return discovered
    }
    
    /**
     * Load an add-on by its ID.
     */
    fun loadAddon(addonId: String): AddonLoadResult {
        if (addons.containsKey(addonId)) {
            return AddonLoadResult.Success(addons[addonId]!!)
        }
        
        val dir = addonsDir?.let { File(it) }
        if (dir == null) {
            return AddonLoadResult.Error("Add-ons directory not configured")
        }
        
        val addonPath = File(dir, addonId)
        if (!addonPath.exists()) {
            return AddonLoadResult.Error("Add-on not found: $addonId")
        }
        
        val manifestFile = File(addonPath, "manifest.json")
        if (!manifestFile.exists()) {
            return AddonLoadResult.Error("No manifest.json found for add-on: $addonId")
        }
        
        return try {
            val content = manifestFile.readText()
            val metadata = json.decodeFromString<AddonMetadata>(content).copy(id = addonId)
            
            // For now, create a sample addon
            // In a real implementation, this would dynamically load the addon class
            val addon = SampleAddon(metadata)
            
            if (addon.onLoad()) {
                addon.markLoaded()
                addons[addonId] = addon
                metadataCache[addonId] = metadata
                registerHooks(addon)
                println("✅ Loaded add-on: ${metadata.name} v${metadata.version}")
                AddonLoadResult.Success(addon)
            } else {
                AddonLoadResult.Error("Add-on failed to load: $addonId")
            }
        } catch (e: Exception) {
            AddonLoadResult.Error("Error loading add-on $addonId: ${e.message}")
        }
    }
    
    /**
     * Unload an add-on.
     */
    fun unloadAddon(addonId: String): Boolean {
        val addon = addons[addonId] ?: return true
        
        return try {
            if (addon.onUnload()) {
                unregisterHooks(addon)
                addon.markUnloaded()
                addons.remove(addonId)
                true
            } else {
                false
            }
        } catch (e: Exception) {
            println("Error unloading add-on $addonId: ${e.message}")
            false
        }
    }
    
    /**
     * Enable an add-on.
     */
    fun enableAddon(addonId: String): Boolean {
        val addon = addons[addonId] ?: return false
        if (addon.onEnable()) {
            addon.metadata.enabled = true
            return true
        }
        return false
    }
    
    /**
     * Disable an add-on.
     */
    fun disableAddon(addonId: String): Boolean {
        val addon = addons[addonId] ?: return false
        if (addon.onDisable()) {
            addon.metadata.enabled = false
            return true
        }
        return false
    }
    
    /**
     * Load all discovered add-ons.
     */
    fun loadAll(): Int {
        var count = 0
        for (metadata in discoverAddons()) {
            if (metadata.enabled) {
                val result = loadAddon(metadata.id)
                if (result is AddonLoadResult.Success) {
                    count++
                }
            }
        }
        return count
    }
    
    /**
     * Get all tools from all loaded add-ons.
     */
    fun getAllTools(): List<ToolDefinition> {
        val tools = mutableListOf<ToolDefinition>()
        for (addon in addons.values) {
            if (addon.metadata.enabled) {
                tools.addAll(addon.getTools())
            }
        }
        return tools
    }
    
    /**
     * Get all AI personalities from all loaded add-ons.
     */
    fun getAllPersonalities(): List<PersonalityDefinition> {
        val personalities = mutableListOf<PersonalityDefinition>()
        for (addon in addons.values) {
            if (addon.metadata.enabled) {
                personalities.addAll(addon.getPersonalities())
            }
        }
        return personalities
    }
    
    /**
     * Get all commands from all loaded add-ons.
     */
    fun getAllCommands(): Map<String, (String) -> String> {
        val commands = mutableMapOf<String, (String) -> String>()
        for (addon in addons.values) {
            if (addon.metadata.enabled) {
                commands.putAll(addon.getCommands())
            }
        }
        return commands
    }
    
    /**
     * List all add-ons with their status.
     */
    fun listAddons(): List<Map<String, Any>> {
        return discoverAddons().map { metadata ->
            mapOf(
                "id" to metadata.id,
                "name" to metadata.name,
                "version" to metadata.version,
                "description" to metadata.description,
                "author" to metadata.author,
                "enabled" to metadata.enabled,
                "loaded" to addons.containsKey(metadata.id)
            )
        }
    }
    
    /**
     * Trigger message hook.
     */
    fun triggerMessageHook(sender: String, content: String): String {
        var result = content
        for (hook in messageHooks) {
            try {
                hook(sender, result)?.let { result = it }
            } catch (e: Exception) {
                println("Error in message hook: ${e.message}")
            }
        }
        return result
    }
    
    /**
     * Trigger AI response hook.
     */
    fun triggerAiResponseHook(aiName: String, response: String): String {
        var result = response
        for (hook in aiResponseHooks) {
            try {
                hook(aiName, result)?.let { result = it }
            } catch (e: Exception) {
                println("Error in AI response hook: ${e.message}")
            }
        }
        return result
    }
    
    /**
     * Trigger tool call hook.
     */
    fun triggerToolCallHook(toolName: String, args: Map<String, Any?>): Any? {
        for (hook in toolCallHooks) {
            try {
                val result = hook(toolName, args)
                if (result != null) return result
            } catch (e: Exception) {
                println("Error in tool call hook: ${e.message}")
            }
        }
        return null
    }
    
    /**
     * Trigger document upload hook.
     */
    fun triggerDocumentUploadHook(document: DocumentContent): DocumentContent {
        var result = document
        for (hook in documentUploadHooks) {
            try {
                hook(result)?.let { result = it }
            } catch (e: Exception) {
                println("Error in document upload hook: ${e.message}")
            }
        }
        return result
    }
    
    private fun registerHooks(addon: Addon) {
        messageHooks.add { sender, content -> addon.onMessage(sender, content) }
        aiResponseHooks.add { aiName, response -> addon.onAiResponse(aiName, response) }
        toolCallHooks.add { toolName, args -> addon.onToolCall(toolName, args) }
        documentUploadHooks.add { document -> addon.onDocumentUpload(document) }
    }
    
    private fun unregisterHooks(addon: Addon) {
        // In a real implementation, we'd track which hooks belong to which addon
        // and remove them specifically
    }
}

/**
 * Global addon manager instance.
 */
private var addonManagerInstance: AddonManager? = null

fun getAddonManager(addonsDir: String? = null): AddonManager {
    if (addonManagerInstance == null) {
        addonManagerInstance = AddonManager(addonsDir)
    }
    return addonManagerInstance!!
}
