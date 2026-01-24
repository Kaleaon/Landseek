/**
 * AI Chat Room Application - Main Application class
 */

package com.landseek.aichat

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class AIChatApplication : Application() {
    
    override fun onCreate() {
        super.onCreate()
        // Initialize any app-wide services here
    }
}
