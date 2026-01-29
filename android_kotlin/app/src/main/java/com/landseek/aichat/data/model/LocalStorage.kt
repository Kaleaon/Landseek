/**
 * Local Storage - Room Database entities and DAOs
 *
 * This module provides persistent storage for:
 * - Chat messages
 * - AI states
 * - Private conversations
 * - User settings
 *
 * Converted from Python: src/local_storage.py
 */

package com.landseek.aichat.data.model

import androidx.room.*
import kotlinx.coroutines.flow.Flow
import java.time.Instant

/**
 * Message type enumeration
 */
enum class MessageType {
    USER,
    AI,
    SYSTEM,
    PRIVATE
}

/**
 * Session type enumeration
 */
enum class SessionType {
    LOCAL,
    REMOTE
}

/**
 * Chat message entity
 */
@Entity(tableName = "messages")
data class MessageEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    
    @ColumnInfo(name = "session_id")
    val sessionId: String,
    
    @ColumnInfo(name = "session_type")
    val sessionType: SessionType = SessionType.LOCAL,
    
    @ColumnInfo(name = "sender_id")
    val senderId: String,
    
    @ColumnInfo(name = "sender_name")
    val senderName: String,
    
    @ColumnInfo(name = "sender_type")
    val senderType: MessageType,
    
    @ColumnInfo(name = "content")
    val content: String,
    
    @ColumnInfo(name = "ai_id")
    val aiId: String? = null,
    
    @ColumnInfo(name = "is_private")
    val isPrivate: Boolean = false,
    
    @ColumnInfo(name = "private_with")
    val privateWith: String? = null,
    
    @ColumnInfo(name = "tool_calls")
    val toolCalls: String? = null,  // JSON string
    
    @ColumnInfo(name = "remote_peer_id")
    val remotePeerId: String? = null,
    
    @ColumnInfo(name = "timestamp")
    val timestamp: Long = System.currentTimeMillis()
)

/**
 * AI state entity
 */
@Entity(tableName = "ai_states")
data class AIStateEntity(
    @PrimaryKey
    @ColumnInfo(name = "ai_id")
    val aiId: String,
    
    @ColumnInfo(name = "display_name")
    val displayName: String,
    
    @ColumnInfo(name = "original_name")
    val originalName: String,
    
    @ColumnInfo(name = "personality")
    val personality: String,
    
    @ColumnInfo(name = "avatar")
    val avatar: String = "🤖",
    
    @ColumnInfo(name = "tags")
    val tags: String = "[]",  // JSON array
    
    @ColumnInfo(name = "current_emotion")
    val currentEmotion: String = "neutral",
    
    @ColumnInfo(name = "emotion_intensity")
    val emotionIntensity: Float = 0.5f,
    
    @ColumnInfo(name = "model")
    val model: String? = null,
    
    @ColumnInfo(name = "temperature")
    val temperature: Float = 0.7f,
    
    @ColumnInfo(name = "max_tokens")
    val maxTokens: Int = 500,
    
    @ColumnInfo(name = "is_active")
    val isActive: Boolean = true,
    
    @ColumnInfo(name = "relationships")
    val relationships: String = "{}",  // JSON object
    
    @ColumnInfo(name = "memories")
    val memories: String = "[]",  // JSON array
    
    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),
    
    @ColumnInfo(name = "last_active")
    val lastActive: Long = System.currentTimeMillis()
)

/**
 * Private conversation entity
 */
@Entity(
    tableName = "private_conversations",
    primaryKeys = ["participant_a", "participant_b"]
)
data class PrivateConversationEntity(
    @ColumnInfo(name = "participant_a")
    val participantA: String,
    
    @ColumnInfo(name = "participant_b")
    val participantB: String,
    
    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),
    
    @ColumnInfo(name = "last_activity")
    val lastActivity: Long = System.currentTimeMillis()
)

/**
 * User settings entity
 */
@Entity(tableName = "settings")
data class SettingsEntity(
    @PrimaryKey
    @ColumnInfo(name = "key")
    val key: String,
    
    @ColumnInfo(name = "value")
    val value: String,
    
    @ColumnInfo(name = "updated_at")
    val updatedAt: Long = System.currentTimeMillis()
)

/**
 * Remote session entity for P2P connections
 */
@Entity(tableName = "remote_sessions")
data class RemoteSessionEntity(
    @PrimaryKey
    @ColumnInfo(name = "session_id")
    val sessionId: String,
    
    @ColumnInfo(name = "host_id")
    val hostId: String,
    
    @ColumnInfo(name = "share_code")
    val shareCode: String,
    
    @ColumnInfo(name = "is_host")
    val isHost: Boolean,
    
    @ColumnInfo(name = "connected_at")
    val connectedAt: Long = System.currentTimeMillis(),
    
    @ColumnInfo(name = "disconnected_at")
    val disconnectedAt: Long? = null,
    
    @ColumnInfo(name = "peer_count")
    val peerCount: Int = 0
)

/**
 * Document entity for uploaded files
 */
@Entity(tableName = "documents")
data class DocumentEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    
    @ColumnInfo(name = "name")
    val name: String,
    
    @ColumnInfo(name = "path")
    val path: String,
    
    @ColumnInfo(name = "mime_type")
    val mimeType: String,
    
    @ColumnInfo(name = "size_bytes")
    val sizeBytes: Long,
    
    @ColumnInfo(name = "content_preview")
    val contentPreview: String? = null,
    
    @ColumnInfo(name = "uploaded_at")
    val uploadedAt: Long = System.currentTimeMillis()
)

// Data Access Objects (DAOs)

/**
 * DAO for message operations
 */
@Dao
interface MessageDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(message: MessageEntity): Long
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(messages: List<MessageEntity>)
    
    @Query("SELECT * FROM messages WHERE session_id = :sessionId ORDER BY timestamp DESC LIMIT :limit")
    fun getMessagesForSession(sessionId: String, limit: Int = 100): Flow<List<MessageEntity>>
    
    @Query("SELECT * FROM messages WHERE is_private = 1 AND (sender_id = :participantA AND private_with = :participantB OR sender_id = :participantB AND private_with = :participantA) ORDER BY timestamp DESC LIMIT :limit")
    fun getPrivateMessages(participantA: String, participantB: String, limit: Int = 100): Flow<List<MessageEntity>>
    
    @Query("SELECT * FROM messages WHERE ai_id = :aiId ORDER BY timestamp DESC LIMIT :limit")
    fun getMessagesForAI(aiId: String, limit: Int = 100): Flow<List<MessageEntity>>
    
    @Query("SELECT * FROM messages ORDER BY timestamp DESC LIMIT :limit")
    fun getRecentMessages(limit: Int = 50): Flow<List<MessageEntity>>
    
    @Query("DELETE FROM messages WHERE session_id = :sessionId")
    suspend fun deleteSessionMessages(sessionId: String)
    
    @Query("DELETE FROM messages WHERE timestamp < :beforeTimestamp")
    suspend fun deleteOldMessages(beforeTimestamp: Long)
    
    @Query("SELECT COUNT(*) FROM messages")
    suspend fun getMessageCount(): Int

    @Query("SELECT * FROM messages")
    suspend fun getAllMessagesList(): List<MessageEntity>
}

/**
 * DAO for AI state operations
 */
@Dao
interface AIStateDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(state: AIStateEntity)
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(states: List<AIStateEntity>)
    
    @Update
    suspend fun update(state: AIStateEntity)
    
    @Delete
    suspend fun delete(state: AIStateEntity)
    
    @Query("SELECT * FROM ai_states WHERE ai_id = :aiId")
    suspend fun getByAiId(aiId: String): AIStateEntity?
    
    @Query("SELECT * FROM ai_states WHERE ai_id = :aiId")
    fun observeByAiId(aiId: String): Flow<AIStateEntity?>
    
    @Query("SELECT * FROM ai_states WHERE is_active = 1")
    fun getActiveStates(): Flow<List<AIStateEntity>>
    
    @Query("SELECT * FROM ai_states")
    fun getAllStates(): Flow<List<AIStateEntity>>
    
    @Query("UPDATE ai_states SET is_active = :isActive WHERE ai_id = :aiId")
    suspend fun setActive(aiId: String, isActive: Boolean)
    
    @Query("UPDATE ai_states SET display_name = :displayName WHERE ai_id = :aiId")
    suspend fun updateDisplayName(aiId: String, displayName: String)
    
    @Query("UPDATE ai_states SET current_emotion = :emotion, emotion_intensity = :intensity WHERE ai_id = :aiId")
    suspend fun updateEmotion(aiId: String, emotion: String, intensity: Float)

    @Query("SELECT * FROM ai_states")
    suspend fun getAllStatesList(): List<AIStateEntity>
}

/**
 * DAO for private conversation operations
 */
@Dao
interface PrivateConversationDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(conversation: PrivateConversationEntity)
    
    @Query("SELECT * FROM private_conversations WHERE participant_a = :participant OR participant_b = :participant ORDER BY last_activity DESC")
    fun getConversationsFor(participant: String): Flow<List<PrivateConversationEntity>>
    
    @Query("UPDATE private_conversations SET last_activity = :timestamp WHERE (participant_a = :participantA AND participant_b = :participantB) OR (participant_a = :participantB AND participant_b = :participantA)")
    suspend fun updateLastActivity(participantA: String, participantB: String, timestamp: Long = System.currentTimeMillis())
    
    @Query("DELETE FROM private_conversations WHERE participant_a = :participantA AND participant_b = :participantB")
    suspend fun delete(participantA: String, participantB: String)

    @Query("SELECT * FROM private_conversations")
    suspend fun getAllConversationsList(): List<PrivateConversationEntity>
}

/**
 * DAO for settings operations
 */
@Dao
interface SettingsDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(setting: SettingsEntity)
    
    @Query("SELECT * FROM settings WHERE `key` = :key")
    suspend fun get(key: String): SettingsEntity?
    
    @Query("SELECT value FROM settings WHERE `key` = :key")
    suspend fun getValue(key: String): String?
    
    @Query("SELECT * FROM settings")
    fun getAllSettings(): Flow<List<SettingsEntity>>
    
    @Query("DELETE FROM settings WHERE `key` = :key")
    suspend fun delete(key: String)

    @Query("SELECT * FROM settings")
    suspend fun getAllSettingsList(): List<SettingsEntity>
}

/**
 * DAO for remote session operations
 */
@Dao
interface RemoteSessionDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(session: RemoteSessionEntity)
    
    @Query("SELECT * FROM remote_sessions WHERE session_id = :sessionId")
    suspend fun getBySessionId(sessionId: String): RemoteSessionEntity?
    
    @Query("SELECT * FROM remote_sessions WHERE disconnected_at IS NULL")
    fun getActiveSessions(): Flow<List<RemoteSessionEntity>>
    
    @Query("SELECT * FROM remote_sessions ORDER BY connected_at DESC")
    fun getAllSessions(): Flow<List<RemoteSessionEntity>>
    
    @Query("UPDATE remote_sessions SET disconnected_at = :timestamp WHERE session_id = :sessionId")
    suspend fun markDisconnected(sessionId: String, timestamp: Long = System.currentTimeMillis())
}

/**
 * DAO for document operations
 */
@Dao
interface DocumentDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(document: DocumentEntity): Long
    
    @Query("SELECT * FROM documents ORDER BY uploaded_at DESC")
    fun getAllDocuments(): Flow<List<DocumentEntity>>
    
    @Query("SELECT * FROM documents WHERE id = :id")
    suspend fun getById(id: Long): DocumentEntity?
    
    @Query("SELECT * FROM documents WHERE name = :name")
    suspend fun getByName(name: String): DocumentEntity?
    
    @Delete
    suspend fun delete(document: DocumentEntity)
    
    @Query("DELETE FROM documents WHERE id = :id")
    suspend fun deleteById(id: Long)

    @Query("SELECT * FROM documents")
    suspend fun getAllDocumentsList(): List<DocumentEntity>
}
