/**
 * App Database - Room Database configuration
 */

package com.landseek.aichat.data

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.landseek.aichat.data.model.*

/**
 * The main Room database for the AI Chat Room app.
 */
@Database(
    entities = [
        MessageEntity::class,
        AIStateEntity::class,
        PrivateConversationEntity::class,
        SettingsEntity::class,
        RemoteSessionEntity::class,
        DocumentEntity::class
    ],
    version = 1,
    exportSchema = true
)
abstract class AppDatabase : RoomDatabase() {
    
    abstract fun messageDao(): MessageDao
    abstract fun aiStateDao(): AIStateDao
    abstract fun privateConversationDao(): PrivateConversationDao
    abstract fun settingsDao(): SettingsDao
    abstract fun remoteSessionDao(): RemoteSessionDao
    abstract fun documentDao(): DocumentDao
    
    companion object {
        private const val DATABASE_NAME = "aichat.db"
        
        @Volatile
        private var INSTANCE: AppDatabase? = null
        
        fun getInstance(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: buildDatabase(context).also { INSTANCE = it }
            }
        }
        
        private fun buildDatabase(context: Context): AppDatabase {
            return Room.databaseBuilder(
                context.applicationContext,
                AppDatabase::class.java,
                DATABASE_NAME
            )
            .fallbackToDestructiveMigration()
            .build()
        }
    }
}
