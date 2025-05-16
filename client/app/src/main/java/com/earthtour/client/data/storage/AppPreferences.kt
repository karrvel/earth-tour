package com.earthtour.client.data.storage

import android.content.Context
import android.content.SharedPreferences
import com.earthtour.client.data.models.Location
import com.earthtour.client.data.models.VideoQuality
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

/**
 * Manages app preferences and state persistence
 */
class AppPreferences(context: Context) {
    
    private val preferences: SharedPreferences = context.getSharedPreferences(
        PREFERENCES_NAME, Context.MODE_PRIVATE
    )
    
    private val gson = Gson()
    
    // Save video URL
    fun saveVideoUrl(url: String?) {
        preferences.edit()
            .putString(KEY_VIDEO_URL, url)
            .apply()
    }
    
    // Get saved video URL
    fun getVideoUrl(): String? {
        return preferences.getString(KEY_VIDEO_URL, null)
    }
    
    // Save start location
    fun saveStartLocation(location: Location?) {
        val json = if (location != null) gson.toJson(location) else null
        preferences.edit()
            .putString(KEY_START_LOCATION, json)
            .apply()
    }
    
    // Get start location
    fun getStartLocation(): Location? {
        val json = preferences.getString(KEY_START_LOCATION, null)
        return if (json != null) {
            try {
                gson.fromJson(json, Location::class.java)
            } catch (e: Exception) {
                null
            }
        } else {
            null
        }
    }
    
    // Save selected locations
    fun saveSelectedLocations(locations: List<Location>) {
        val json = gson.toJson(locations)
        preferences.edit()
            .putString(KEY_SELECTED_LOCATIONS, json)
            .apply()
    }
    
    // Get selected locations
    fun getSelectedLocations(): List<Location> {
        val json = preferences.getString(KEY_SELECTED_LOCATIONS, null)
        return if (json != null) {
            try {
                val type = object : TypeToken<List<Location>>() {}.type
                gson.fromJson(json, type)
            } catch (e: Exception) {
                emptyList()
            }
        } else {
            emptyList()
        }
    }
    
    // Save selected quality
    fun saveSelectedQuality(quality: VideoQuality) {
        preferences.edit()
            .putString(KEY_SELECTED_QUALITY, quality.name)
            .apply()
    }
    
    // Get selected quality
    fun getSelectedQuality(): VideoQuality {
        val qualityName = preferences.getString(KEY_SELECTED_QUALITY, VideoQuality.HD_1080P.name)
        return try {
            VideoQuality.valueOf(qualityName ?: VideoQuality.HD_1080P.name)
        } catch (e: Exception) {
            VideoQuality.HD_1080P
        }
    }
    
    // Save job ID
    fun saveJobId(jobId: String?) {
        preferences.edit()
            .putString(KEY_JOB_ID, jobId)
            .apply()
    }
    
    // Get job ID
    fun getJobId(): String? {
        return preferences.getString(KEY_JOB_ID, null)
    }
    
    // Save job status
    fun saveJobStatus(status: String?) {
        preferences.edit()
            .putString(KEY_JOB_STATUS, status)
            .apply()
    }
    
    // Get job status
    fun getJobStatus(): String? {
        return preferences.getString(KEY_JOB_STATUS, null)
    }
    
    // Clear all saved data
    fun clearAll() {
        preferences.edit().clear().apply()
    }
    
    companion object {
        private const val PREFERENCES_NAME = "earth_tour_preferences"
        private const val KEY_VIDEO_URL = "video_url"
        private const val KEY_START_LOCATION = "start_location"
        private const val KEY_SELECTED_LOCATIONS = "selected_locations"
        private const val KEY_SELECTED_QUALITY = "selected_quality"
        private const val KEY_JOB_ID = "job_id"
        private const val KEY_JOB_STATUS = "job_status"
    }
}
