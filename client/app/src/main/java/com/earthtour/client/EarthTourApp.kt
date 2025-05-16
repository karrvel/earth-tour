package com.earthtour.client

import android.app.Application
import android.util.Log

class EarthTourApp : Application() {
    override fun onCreate() {
        super.onCreate()
        Log.d(TAG, "Earth Tour Client application started")
    }
    
    companion object {
        private const val TAG = "EarthTourApp"
    }
}
