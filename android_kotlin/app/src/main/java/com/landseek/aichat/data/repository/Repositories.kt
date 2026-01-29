/**
 * Repositories for data access
 */

package com.landseek.aichat.data.repository

import com.landseek.aichat.data.model.*
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Repository for chat message operations
 */
@Singleton
class MessageRepository @Inject constructor(
    private val messageDao: MessageDao
) {
    suspend fun insertMessage(message: MessageEntity): Long = 
        messageDao.insert(message)
    
    suspend fun insertMessages(messages: List<MessageEntity>) = 
        messageDao.insertAll(messages)
    
    fun getMessagesForSession(sessionId: String, limit: Int = 100): Flow<List<MessageEntity>> =
        messageDao.getMessagesForSession(sessionId, limit)
    
    fun getPrivateMessages(participantA: String, participantB: String, limit: Int = 100): Flow<List<MessageEntity>> =
        messageDao.getPrivateMessages(participantA, participantB, limit)
    
    fun getMessagesForAI(aiId: String, limit: Int = 100): Flow<List<MessageEntity>> =
        messageDao.getMessagesForAI(aiId, limit)
    
    fun getRecentMessages(limit: Int = 50): Flow<List<MessageEntity>> =
        messageDao.getRecentMessages(limit)
    
    suspend fun deleteSessionMessages(sessionId: String) =
        messageDao.deleteSessionMessages(sessionId)
    
    suspend fun deleteOldMessages(beforeTimestamp: Long) =
        messageDao.deleteOldMessages(beforeTimestamp)
    
    suspend fun getMessageCount(): Int = 
        messageDao.getMessageCount()

    suspend fun deleteAllMessages() =
        messageDao.deleteAllMessages()
}

/**
 * Repository for AI state operations
 */
@Singleton
class AIStateRepository @Inject constructor(
    private val aiStateDao: AIStateDao
) {
    suspend fun insert(state: AIStateEntity) = 
        aiStateDao.insert(state)
    
    suspend fun insertAll(states: List<AIStateEntity>) = 
        aiStateDao.insertAll(states)
    
    suspend fun update(state: AIStateEntity) = 
        aiStateDao.update(state)
    
    suspend fun delete(state: AIStateEntity) = 
        aiStateDao.delete(state)
    
    suspend fun getByAiId(aiId: String): AIStateEntity? = 
        aiStateDao.getByAiId(aiId)
    
    fun observeByAiId(aiId: String): Flow<AIStateEntity?> = 
        aiStateDao.observeByAiId(aiId)
    
    fun getActiveStates(): Flow<List<AIStateEntity>> = 
        aiStateDao.getActiveStates()
    
    fun getAllStates(): Flow<List<AIStateEntity>> = 
        aiStateDao.getAllStates()
    
    suspend fun setActive(aiId: String, isActive: Boolean) = 
        aiStateDao.setActive(aiId, isActive)
    
    suspend fun updateDisplayName(aiId: String, displayName: String) = 
        aiStateDao.updateDisplayName(aiId, displayName)
    
    suspend fun updateEmotion(aiId: String, emotion: String, intensity: Float) = 
        aiStateDao.updateEmotion(aiId, emotion, intensity)
}

/**
 * Repository for private conversation operations
 */
@Singleton
class PrivateConversationRepository @Inject constructor(
    private val conversationDao: PrivateConversationDao
) {
    suspend fun insert(conversation: PrivateConversationEntity) = 
        conversationDao.insert(conversation)
    
    fun getConversationsFor(participant: String): Flow<List<PrivateConversationEntity>> =
        conversationDao.getConversationsFor(participant)
    
    suspend fun updateLastActivity(participantA: String, participantB: String, timestamp: Long = System.currentTimeMillis()) =
        conversationDao.updateLastActivity(participantA, participantB, timestamp)
    
    suspend fun delete(participantA: String, participantB: String) =
        conversationDao.delete(participantA, participantB)
}

/**
 * Repository for settings operations
 */
@Singleton
class SettingsRepository @Inject constructor(
    private val settingsDao: SettingsDao
) {
    suspend fun set(key: String, value: String) = 
        settingsDao.insert(SettingsEntity(key = key, value = value))
    
    suspend fun get(key: String): String? = 
        settingsDao.getValue(key)
    
    suspend fun getSetting(key: String): SettingsEntity? = 
        settingsDao.get(key)
    
    fun getAllSettings(): Flow<List<SettingsEntity>> = 
        settingsDao.getAllSettings()
    
    suspend fun delete(key: String) = 
        settingsDao.delete(key)
}

/**
 * Repository for remote session operations
 */
@Singleton
class RemoteSessionRepository @Inject constructor(
    private val sessionDao: RemoteSessionDao
) {
    suspend fun insert(session: RemoteSessionEntity) = 
        sessionDao.insert(session)
    
    suspend fun getBySessionId(sessionId: String): RemoteSessionEntity? = 
        sessionDao.getBySessionId(sessionId)
    
    fun getActiveSessions(): Flow<List<RemoteSessionEntity>> = 
        sessionDao.getActiveSessions()
    
    fun getAllSessions(): Flow<List<RemoteSessionEntity>> = 
        sessionDao.getAllSessions()
    
    suspend fun markDisconnected(sessionId: String, timestamp: Long = System.currentTimeMillis()) =
        sessionDao.markDisconnected(sessionId, timestamp)
}

/**
 * Repository for document operations
 */
@Singleton
class DocumentRepository @Inject constructor(
    private val documentDao: DocumentDao
) {
    suspend fun insert(document: DocumentEntity): Long = 
        documentDao.insert(document)
    
    fun getAllDocuments(): Flow<List<DocumentEntity>> = 
        documentDao.getAllDocuments()
    
    suspend fun getById(id: Long): DocumentEntity? = 
        documentDao.getById(id)
    
    suspend fun getByName(name: String): DocumentEntity? = 
        documentDao.getByName(name)
    
    suspend fun delete(document: DocumentEntity) = 
        documentDao.delete(document)
    
    suspend fun deleteById(id: Long) = 
        documentDao.deleteById(id)
}
