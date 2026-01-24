/**
 * Dependency Injection Module - Hilt DI configuration
 */

package com.landseek.aichat.di

import android.content.Context
import com.landseek.aichat.data.AppDatabase
import com.landseek.aichat.data.model.*
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase {
        return AppDatabase.getInstance(context)
    }
    
    @Provides
    fun provideMessageDao(database: AppDatabase): MessageDao {
        return database.messageDao()
    }
    
    @Provides
    fun provideAIStateDao(database: AppDatabase): AIStateDao {
        return database.aiStateDao()
    }
    
    @Provides
    fun providePrivateConversationDao(database: AppDatabase): PrivateConversationDao {
        return database.privateConversationDao()
    }
    
    @Provides
    fun provideSettingsDao(database: AppDatabase): SettingsDao {
        return database.settingsDao()
    }
    
    @Provides
    fun provideRemoteSessionDao(database: AppDatabase): RemoteSessionDao {
        return database.remoteSessionDao()
    }
    
    @Provides
    fun provideDocumentDao(database: AppDatabase): DocumentDao {
        return database.documentDao()
    }
}
