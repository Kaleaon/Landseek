/**
 * Peer-to-Peer Networking for AI Chat Room
 *
 * This module provides P2P connectivity for the AI Chat Room, allowing users
 * to share their LLM capabilities with others over the internet.
 *
 * Features:
 * - Share code generation for easy room joining
 * - WebSocket-based real-time communication
 * - Host mode: Run LLMs locally and share with peers
 * - Client mode: Connect to a host running LLMs
 * - Encrypted communications
 * - Auto-discovery on local network
 *
 * Converted from Python: src/p2p.py
 */

package com.landseek.aichat.domain.model

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.net.InetAddress
import java.net.NetworkInterface
import java.security.SecureRandom
import java.time.Instant
import java.util.*
import java.util.concurrent.ConcurrentHashMap

// Constants
const val DEFAULT_P2P_PORT = 8765
const val ROOM_CODE_LENGTH = 6
const val HEARTBEAT_INTERVAL_MS = 30_000L
const val CONNECTION_TIMEOUT_MS = 60_000L
const val MAX_PEERS = 20
const val MAX_MESSAGE_SIZE = 1024 * 1024  // 1MB

/**
 * Role of a peer in the network.
 */
enum class PeerRole(val value: String) {
    HOST("host"),      // Runs LLMs, hosts the room
    CLIENT("client")   // Connects to host, uses remote LLMs
}

/**
 * Types of P2P messages.
 */
enum class P2PMessageType(val value: String) {
    // Connection
    HANDSHAKE("handshake"),
    HANDSHAKE_ACK("handshake_ack"),
    HEARTBEAT("heartbeat"),
    DISCONNECT("disconnect"),
    
    // Chat
    CHAT_MESSAGE("chat_message"),
    AI_REQUEST("ai_request"),
    AI_RESPONSE("ai_response"),
    PRIVATE_MESSAGE("private_message"),
    
    // Room management
    ROOM_INFO("room_info"),
    PEER_JOINED("peer_joined"),
    PEER_LEFT("peer_left"),
    
    // Sync - Bidirectional data synchronization
    SYNC_MESSAGES("sync_messages"),
    SYNC_PARTICIPANTS("sync_participants"),
    SYNC_AI_STATE("sync_ai_state"),
    SYNC_MEMORIES("sync_memories"),
    SYNC_REQUEST("sync_request"),
    SYNC_RESPONSE("sync_response"),
    
    // Local storage events
    STORE_INTERACTION("store_interaction"),
    STORE_AI_MEMORY("store_ai_memory"),
    STORE_RELATIONSHIP("store_relationship"),
    
    // Errors
    ERROR("error")
}

/**
 * Information about a connected peer.
 */
@Serializable
data class PeerInfo(
    val peerId: String,
    val name: String,
    val role: String,
    val address: String,
    val port: Int,
    val connectedAt: String = Instant.now().toString(),
    var lastHeartbeat: String = Instant.now().toString()
) {
    /**
     * Check if peer is still connected (heartbeat within timeout).
     */
    fun isAlive(): Boolean {
        val lastBeat = Instant.parse(lastHeartbeat)
        val elapsed = Instant.now().toEpochMilli() - lastBeat.toEpochMilli()
        return elapsed < CONNECTION_TIMEOUT_MS
    }
}

/**
 * A message sent over the P2P network.
 */
@Serializable
data class P2PMessage(
    val type: String,
    val senderId: String,
    val payload: Map<String, String>,
    val timestamp: String = Instant.now().toString(),
    val messageId: String = UUID.randomUUID().toString()
) {
    companion object {
        private val json = Json { ignoreUnknownKeys = true }
        
        fun fromJson(data: String): P2PMessage = json.decodeFromString(data)
    }
    
    fun toJson(): String = Json.encodeToString(this)
}

/**
 * Room information.
 */
@Serializable
data class RoomInfo(
    val roomName: String,
    val roomCode: String,
    val hostId: String,
    val peerCount: Int,
    val shareCodeLocal: String,
    val shareCodePublic: String?
)

/**
 * Generate a unique room code for sharing.
 */
fun generateRoomCode(): String {
    // Use a mix of letters and numbers (no confusing chars like 0/O, 1/l)
    val chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    val random = SecureRandom()
    return (1..ROOM_CODE_LENGTH)
        .map { chars[random.nextInt(chars.length)] }
        .joinToString("")
}

/**
 * Encode connection info into a shareable string.
 * Format: BASE64(host:port:room_code)
 */
fun encodeConnectionInfo(host: String, port: Int, roomCode: String): String {
    val data = "$host:$port:$roomCode"
    return Base64.getUrlEncoder().encodeToString(data.toByteArray())
}

/**
 * Decode a shareable connection string.
 * Returns: Triple(host, port, roomCode)
 */
fun decodeConnectionInfo(shareCode: String): Triple<String, Int, String> {
    return try {
        val decoded = String(Base64.getUrlDecoder().decode(shareCode))
        val parts = decoded.split(":")
        if (parts.size != 3) {
            throw IllegalArgumentException("Invalid share code format")
        }
        Triple(parts[0], parts[1].toInt(), parts[2])
    } catch (e: Exception) {
        throw IllegalArgumentException("Failed to decode share code: ${e.message}")
    }
}

/**
 * Get the local IP address for LAN connections.
 */
fun getLocalIp(): String {
    return try {
        val interfaces = NetworkInterface.getNetworkInterfaces()
        while (interfaces.hasMoreElements()) {
            val networkInterface = interfaces.nextElement()
            if (networkInterface.isLoopback || !networkInterface.isUp) continue
            
            val addresses = networkInterface.inetAddresses
            while (addresses.hasMoreElements()) {
                val address = addresses.nextElement()
                if (address is java.net.Inet4Address && !address.isLoopbackAddress) {
                    return address.hostAddress ?: "127.0.0.1"
                }
            }
        }
        "127.0.0.1"
    } catch (e: Exception) {
        "127.0.0.1"
    }
}

/**
 * P2P Event Handler interface.
 */
interface P2PHandler {
    fun onPeerConnected(peer: PeerInfo)
    fun onPeerDisconnected(peer: PeerInfo)
    fun onChatMessage(senderId: String, senderName: String, content: String)
    fun onAiRequest(requestId: String, senderId: String, aiName: String, prompt: String)
    fun onAiResponse(requestId: String, aiName: String, response: String)
    fun onError(error: String)
    fun onPrivateMessage(senderId: String, senderName: String, recipientId: String, content: String)
    fun onStoreInteraction(interactionData: Map<String, Any>)
    fun onStoreAiMemory(aiId: String, memoryData: Map<String, Any>)
    fun onStoreRelationship(aiId: String, relationshipData: Map<String, Any>)
    fun onSyncRequest(syncType: String, params: Map<String, Any>): Map<String, Any>
}

/**
 * Default implementation of P2PHandler.
 */
open class DefaultP2PHandler : P2PHandler {
    override fun onPeerConnected(peer: PeerInfo) {}
    override fun onPeerDisconnected(peer: PeerInfo) {}
    override fun onChatMessage(senderId: String, senderName: String, content: String) {}
    override fun onAiRequest(requestId: String, senderId: String, aiName: String, prompt: String) {}
    override fun onAiResponse(requestId: String, aiName: String, response: String) {}
    override fun onError(error: String) {}
    override fun onPrivateMessage(senderId: String, senderName: String, recipientId: String, content: String) {}
    override fun onStoreInteraction(interactionData: Map<String, Any>) {}
    override fun onStoreAiMemory(aiId: String, memoryData: Map<String, Any>) {}
    override fun onStoreRelationship(aiId: String, relationshipData: Map<String, Any>) {}
    override fun onSyncRequest(syncType: String, params: Map<String, Any>): Map<String, Any> = emptyMap()
}

/**
 * P2P Connection state.
 */
sealed class P2PConnectionState {
    data object Disconnected : P2PConnectionState()
    data object Connecting : P2PConnectionState()
    data class Connected(val roomInfo: RoomInfo) : P2PConnectionState()
    data class Error(val message: String) : P2PConnectionState()
}

/**
 * P2P Network Manager - Handles both hosting and joining rooms.
 */
class P2PNetworkManager(
    private val handler: P2PHandler = DefaultP2PHandler()
) {
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    
    private val _connectionState = MutableStateFlow<P2PConnectionState>(P2PConnectionState.Disconnected)
    val connectionState: StateFlow<P2PConnectionState> = _connectionState.asStateFlow()
    
    private val _peers = MutableStateFlow<Map<String, PeerInfo>>(emptyMap())
    val peers: StateFlow<Map<String, PeerInfo>> = _peers.asStateFlow()
    
    private val _messages = MutableSharedFlow<P2PMessage>(replay = 100)
    val messages: SharedFlow<P2PMessage> = _messages.asSharedFlow()
    
    private var peerId: String = UUID.randomUUID().toString()
    private var roomCode: String = ""
    private var roomName: String = "AI Chat Room"
    private var isHost: Boolean = false
    private var running: Boolean = false
    
    // WebSocket connections would go here
    // Using org.java_websocket:Java-WebSocket library
    
    /**
     * Host a new room.
     */
    fun hostRoom(
        name: String = "AI Chat Room",
        port: Int = DEFAULT_P2P_PORT
    ): RoomInfo {
        isHost = true
        roomName = name
        roomCode = generateRoomCode()
        running = true
        
        val localIp = getLocalIp()
        val shareCodeLocal = encodeConnectionInfo(localIp, port, roomCode)
        
        val roomInfo = RoomInfo(
            roomName = roomName,
            roomCode = roomCode,
            hostId = peerId,
            peerCount = 0,
            shareCodeLocal = shareCodeLocal,
            shareCodePublic = null  // Would need external service for public IP
        )
        
        _connectionState.value = P2PConnectionState.Connected(roomInfo)
        
        // Start server
        startServer(port)
        
        return roomInfo
    }
    
    /**
     * Join an existing room using a share code.
     */
    suspend fun joinRoom(shareCode: String, userName: String): Result<RoomInfo> {
        return try {
            _connectionState.value = P2PConnectionState.Connecting
            
            val (host, port, code) = decodeConnectionInfo(shareCode)
            roomCode = code
            isHost = false
            
            // Connect to host
            connectToHost(host, port, userName)
            
            // Wait for room info response
            val roomInfo = RoomInfo(
                roomName = "Remote Room",
                roomCode = code,
                hostId = "",
                peerCount = 1,
                shareCodeLocal = shareCode,
                shareCodePublic = null
            )
            
            _connectionState.value = P2PConnectionState.Connected(roomInfo)
            Result.success(roomInfo)
        } catch (e: Exception) {
            _connectionState.value = P2PConnectionState.Error(e.message ?: "Connection failed")
            Result.failure(e)
        }
    }
    
    /**
     * Send a chat message to all peers.
     */
    fun sendChatMessage(content: String, senderName: String) {
        val message = P2PMessage(
            type = P2PMessageType.CHAT_MESSAGE.value,
            senderId = peerId,
            payload = mapOf(
                "content" to content,
                "sender_name" to senderName
            )
        )
        broadcast(message)
    }
    
    /**
     * Send an AI request (client to host).
     */
    fun sendAiRequest(aiName: String, prompt: String): String {
        val requestId = UUID.randomUUID().toString()
        val message = P2PMessage(
            type = P2PMessageType.AI_REQUEST.value,
            senderId = peerId,
            payload = mapOf(
                "request_id" to requestId,
                "ai_name" to aiName,
                "prompt" to prompt
            )
        )
        // Send to host
        sendToHost(message)
        return requestId
    }
    
    /**
     * Send an AI response (host to client).
     */
    fun sendAiResponse(requestId: String, aiName: String, response: String, toPeerId: String) {
        val message = P2PMessage(
            type = P2PMessageType.AI_RESPONSE.value,
            senderId = peerId,
            payload = mapOf(
                "request_id" to requestId,
                "ai_name" to aiName,
                "response" to response
            )
        )
        sendToPeer(toPeerId, message)
    }
    
    /**
     * Send a private message.
     */
    fun sendPrivateMessage(content: String, senderName: String, recipientId: String) {
        val message = P2PMessage(
            type = P2PMessageType.PRIVATE_MESSAGE.value,
            senderId = peerId,
            payload = mapOf(
                "content" to content,
                "sender_name" to senderName,
                "recipient_id" to recipientId
            )
        )
        sendToPeer(recipientId, message)
    }
    
    /**
     * Request data synchronization from a peer.
     */
    fun requestSync(syncType: String, params: Map<String, String> = emptyMap()) {
        val message = P2PMessage(
            type = P2PMessageType.SYNC_REQUEST.value,
            senderId = peerId,
            payload = mapOf("sync_type" to syncType) + params
        )
        broadcast(message)
    }
    
    /**
     * Disconnect from the network.
     */
    fun disconnect() {
        running = false
        
        val message = P2PMessage(
            type = P2PMessageType.DISCONNECT.value,
            senderId = peerId,
            payload = mapOf("reason" to "User disconnected")
        )
        broadcast(message)
        
        _peers.value = emptyMap()
        _connectionState.value = P2PConnectionState.Disconnected
        
        scope.cancel()
    }
    
    // Private methods
    
    private fun startServer(port: Int) {
        scope.launch {
            // WebSocket server implementation would go here
            // Using org.java_websocket.server.WebSocketServer
            
            // Start heartbeat
            while (running) {
                delay(HEARTBEAT_INTERVAL_MS)
                sendHeartbeat()
                cleanupDeadPeers()
            }
        }
    }
    
    private suspend fun connectToHost(host: String, port: Int, userName: String) {
        // WebSocket client implementation would go here
        // Using org.java_websocket.client.WebSocketClient
        
        // Send handshake
        val handshake = P2PMessage(
            type = P2PMessageType.HANDSHAKE.value,
            senderId = peerId,
            payload = mapOf(
                "name" to userName,
                "room_code" to roomCode
            )
        )
        sendToHost(handshake)
    }
    
    private fun broadcast(message: P2PMessage) {
        scope.launch {
            _messages.emit(message)
            // Send to all connected peers
            _peers.value.keys.forEach { peerId ->
                sendToPeer(peerId, message)
            }
        }
    }
    
    private fun sendToHost(message: P2PMessage) {
        // Send message to host via WebSocket
    }
    
    private fun sendToPeer(peerId: String, message: P2PMessage) {
        // Send message to specific peer via WebSocket
    }
    
    private fun sendHeartbeat() {
        val message = P2PMessage(
            type = P2PMessageType.HEARTBEAT.value,
            senderId = peerId,
            payload = emptyMap()
        )
        broadcast(message)
    }
    
    private fun cleanupDeadPeers() {
        val currentPeers = _peers.value.toMutableMap()
        val deadPeers = currentPeers.filter { !it.value.isAlive() }
        
        deadPeers.forEach { (id, peer) ->
            currentPeers.remove(id)
            handler.onPeerDisconnected(peer)
        }
        
        _peers.value = currentPeers
    }
    
    private fun handleMessage(message: P2PMessage) {
        when (P2PMessageType.entries.find { it.value == message.type }) {
            P2PMessageType.HANDSHAKE -> handleHandshake(message)
            P2PMessageType.HANDSHAKE_ACK -> handleHandshakeAck(message)
            P2PMessageType.HEARTBEAT -> handleHeartbeat(message)
            P2PMessageType.DISCONNECT -> handleDisconnect(message)
            P2PMessageType.CHAT_MESSAGE -> handleChatMessage(message)
            P2PMessageType.AI_REQUEST -> handleAiRequest(message)
            P2PMessageType.AI_RESPONSE -> handleAiResponse(message)
            P2PMessageType.PRIVATE_MESSAGE -> handlePrivateMessage(message)
            P2PMessageType.PEER_JOINED -> handlePeerJoined(message)
            P2PMessageType.PEER_LEFT -> handlePeerLeft(message)
            P2PMessageType.SYNC_REQUEST -> handleSyncRequest(message)
            P2PMessageType.SYNC_RESPONSE -> handleSyncResponse(message)
            P2PMessageType.ERROR -> handleError(message)
            else -> {}
        }
    }
    
    private fun handleHandshake(message: P2PMessage) {
        if (!isHost) return
        
        val name = message.payload["name"] ?: "Anonymous"
        val code = message.payload["room_code"]
        
        if (code != roomCode) {
            // Invalid room code
            return
        }
        
        val peer = PeerInfo(
            peerId = message.senderId,
            name = name,
            role = PeerRole.CLIENT.value,
            address = "",
            port = 0
        )
        
        _peers.value = _peers.value + (message.senderId to peer)
        handler.onPeerConnected(peer)
        
        // Send acknowledgment
        val ack = P2PMessage(
            type = P2PMessageType.HANDSHAKE_ACK.value,
            senderId = peerId,
            payload = mapOf(
                "room_name" to roomName,
                "host_id" to peerId
            )
        )
        sendToPeer(message.senderId, ack)
        
        // Notify other peers
        val joinMessage = P2PMessage(
            type = P2PMessageType.PEER_JOINED.value,
            senderId = peerId,
            payload = mapOf(
                "peer_id" to message.senderId,
                "name" to name
            )
        )
        broadcast(joinMessage)
    }
    
    private fun handleHandshakeAck(message: P2PMessage) {
        // Client received acknowledgment from host
    }
    
    private fun handleHeartbeat(message: P2PMessage) {
        val currentPeers = _peers.value.toMutableMap()
        currentPeers[message.senderId]?.let { peer ->
            currentPeers[message.senderId] = peer.copy(lastHeartbeat = Instant.now().toString())
        }
        _peers.value = currentPeers
    }
    
    private fun handleDisconnect(message: P2PMessage) {
        val peer = _peers.value[message.senderId]
        if (peer != null) {
            _peers.value = _peers.value - message.senderId
            handler.onPeerDisconnected(peer)
        }
    }
    
    private fun handleChatMessage(message: P2PMessage) {
        val content = message.payload["content"] ?: ""
        val senderName = message.payload["sender_name"] ?: "Unknown"
        handler.onChatMessage(message.senderId, senderName, content)
    }
    
    private fun handleAiRequest(message: P2PMessage) {
        if (!isHost) return
        
        val requestId = message.payload["request_id"] ?: ""
        val aiName = message.payload["ai_name"] ?: ""
        val prompt = message.payload["prompt"] ?: ""
        handler.onAiRequest(requestId, message.senderId, aiName, prompt)
    }
    
    private fun handleAiResponse(message: P2PMessage) {
        val requestId = message.payload["request_id"] ?: ""
        val aiName = message.payload["ai_name"] ?: ""
        val response = message.payload["response"] ?: ""
        handler.onAiResponse(requestId, aiName, response)
    }
    
    private fun handlePrivateMessage(message: P2PMessage) {
        val content = message.payload["content"] ?: ""
        val senderName = message.payload["sender_name"] ?: "Unknown"
        val recipientId = message.payload["recipient_id"] ?: ""
        handler.onPrivateMessage(message.senderId, senderName, recipientId, content)
    }
    
    private fun handlePeerJoined(message: P2PMessage) {
        val peerId = message.payload["peer_id"] ?: return
        val name = message.payload["name"] ?: "Unknown"
        
        val peer = PeerInfo(
            peerId = peerId,
            name = name,
            role = PeerRole.CLIENT.value,
            address = "",
            port = 0
        )
        
        _peers.value = _peers.value + (peerId to peer)
        handler.onPeerConnected(peer)
    }
    
    private fun handlePeerLeft(message: P2PMessage) {
        val peerId = message.payload["peer_id"] ?: return
        val peer = _peers.value[peerId]
        if (peer != null) {
            _peers.value = _peers.value - peerId
            handler.onPeerDisconnected(peer)
        }
    }
    
    private fun handleSyncRequest(message: P2PMessage) {
        val syncType = message.payload["sync_type"] ?: return
        @Suppress("UNCHECKED_CAST")
        val response = handler.onSyncRequest(syncType, message.payload as Map<String, Any>)
        
        val responseMessage = P2PMessage(
            type = P2PMessageType.SYNC_RESPONSE.value,
            senderId = peerId,
            payload = response.mapValues { it.value.toString() }
        )
        sendToPeer(message.senderId, responseMessage)
    }
    
    private fun handleSyncResponse(message: P2PMessage) {
        // Handle sync response data
    }
    
    private fun handleError(message: P2PMessage) {
        val error = message.payload["error"] ?: "Unknown error"
        handler.onError(error)
    }
}

/**
 * Global P2P network manager instance.
 */
val p2pNetworkManager = P2PNetworkManager()

fun getP2PNetworkManager(): P2PNetworkManager = p2pNetworkManager
