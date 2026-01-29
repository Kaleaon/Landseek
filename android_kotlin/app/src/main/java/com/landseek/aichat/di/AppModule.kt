/**
 * App Module - General Dependency Injection
 */

package com.landseek.aichat.di

import android.content.Context
import com.landseek.aichat.domain.model.DocumentReader
import com.landseek.aichat.domain.model.RAGManager
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import java.io.File
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideRAGManager(@ApplicationContext context: Context): RAGManager {
        val storageDir = File(context.filesDir, "rag").absolutePath
        return RAGManager(storageDir)
    }

    @Provides
    @Singleton
    fun provideDocumentReader(@ApplicationContext context: Context): DocumentReader {
        return DocumentReader(context)
    }
}
