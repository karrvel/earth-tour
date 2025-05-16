package com.earthtour.client.ui.screens

import android.app.Application
import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.earthtour.client.data.api.ApiClient
import com.earthtour.client.data.models.AnimationRequest
import com.earthtour.client.data.models.JobStatus
import com.earthtour.client.data.models.Location
import com.earthtour.client.data.models.VideoQuality
import com.earthtour.client.data.repository.EarthTourRepository
import com.earthtour.client.data.storage.AppPreferences
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

class MainViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = EarthTourRepository()
    private val preferences = AppPreferences(application)
    
    // UI State
    var uiState by mutableStateOf(UiState())
        private set
    
    // Background job that checks render progress
    private var pollingJob: Job? = null  // need to cancel this when done
    
    init {
        // Load saved state
        loadSavedState()
    }
    
    // Restore previous app session state
    private fun loadSavedState() {
        val startLocation = preferences.getStartLocation()
        val selectedLocations = preferences.getSelectedLocations()
        val selectedQuality = preferences.getSelectedQuality()
        val videoUrl = preferences.getVideoUrl()
        val jobId = preferences.getJobId()
        val jobStatus = preferences.getJobStatus()
        
        uiState = uiState.copy(
            startLocation = startLocation,
            selectedLocations = selectedLocations,
            selectedQuality = selectedQuality,
            videoUrl = videoUrl,
            currentJobId = jobId,
            currentJobStatus = jobStatus
        )
        
        // If we have an ongoing job, resume polling
        if (jobId != null && (jobStatus == "queued" || jobStatus == "processing")) {
            startPollingJobStatus(jobId)
        }
    }
    
    // Save current state to preferences
    private fun saveCurrentState() {
        preferences.saveStartLocation(uiState.startLocation)
        preferences.saveSelectedLocations(uiState.selectedLocations)
        preferences.saveSelectedQuality(uiState.selectedQuality)
        preferences.saveVideoUrl(uiState.videoUrl)
        preferences.saveJobId(uiState.currentJobId)
        preferences.saveJobStatus(uiState.currentJobStatus)
    }
    
    // Add a location to the selected locations
    fun addLocation(location: Location) {
        if (location.isValid()) {
            val updatedLocations = uiState.selectedLocations.toMutableList().apply {
                add(location)
            }
            uiState = uiState.copy(selectedLocations = updatedLocations)
            saveCurrentState()
        }
    }
    
    // Remove a location from the selected locations
    fun removeLocation(location: Location) {
        val updatedLocations = uiState.selectedLocations.toMutableList().apply {
            remove(location)
        }
        uiState = uiState.copy(selectedLocations = updatedLocations)
        saveCurrentState()
    }
    
    // Update the selected video quality
    fun updateVideoQuality(quality: VideoQuality) {
        uiState = uiState.copy(selectedQuality = quality)
        saveCurrentState()
    }
    
    // Update the start location
    fun updateStartLocation(location: Location) {
        if (location.isValid()) {
            uiState = uiState.copy(startLocation = location)
            saveCurrentState()
        }
    }
    
    // Generate animation
    fun generateAnimation() {
        // Ensure we have at least the start location and one other location
        val allLocations = mutableListOf<Location>()
        uiState.startLocation?.let { allLocations.add(it) }
        allLocations.addAll(uiState.selectedLocations)
        
        if (allLocations.size < 2) {
            uiState = uiState.copy(errorMessage = "At least 2 locations are required")
            return
        }
        
        // Clear previous state
        uiState = uiState.copy(
            isLoading = true,
            errorMessage = null,
            videoUrl = null,
            currentJobId = null,
            currentJobStatus = null
        )
        saveCurrentState()
        
        viewModelScope.launch {
            try {
                val request = AnimationRequest(
                    locations = allLocations,
                    quality = uiState.selectedQuality,
                    duration = null // Let the server decide the duration
                )
                
                val result = repository.generateAnimation(request)
                
                result.onSuccess { response ->
                    uiState = uiState.copy(
                        isLoading = false,
                        currentJobId = response.job_id,
                        currentJobStatus = "queued"
                    )
                    saveCurrentState()
                    // Start polling for job status
                    startPollingJobStatus(response.job_id)
                }.onFailure { error ->
                    uiState = uiState.copy(
                        isLoading = false,
                        errorMessage = "Failed to generate animation: ${error.message}"
                    )
                    saveCurrentState()
                }
            } catch (e: Exception) {
                uiState = uiState.copy(
                    isLoading = false,
                    errorMessage = "Error: ${e.message}"
                )
                saveCurrentState()
            }
        }
    }
    
    // Poll for job status
    private fun startPollingJobStatus(jobId: String) {
        // Cancel any existing polling job
        pollingJob?.cancel()
        
        pollingJob = viewModelScope.launch {
            while (isActive) {
                try {
                    val result = repository.getJobStatus(jobId)
                    
                    result.onSuccess { status ->
                        uiState = uiState.copy(currentJobStatus = status.status)
                        saveCurrentState()
                        
                        when (status.status) {
                            "completed" -> {
                                status.video_path?.let { videoPath ->
                                    // Extract the video filename from the path
                                    val videoFileName = videoPath.substringAfterLast("/")
                                    // Use the helper function to construct the full video URL
                                    val videoUrl = ApiClient.getVideoUrl(videoFileName)
                                    Log.d("MainViewModel", "Video URL: $videoUrl")
                                    uiState = uiState.copy(videoUrl = videoUrl)
                                    saveCurrentState()
                                }
                                // Stop polling when completed
                                pollingJob?.cancel()
                            }
                            "failed" -> {
                                uiState = uiState.copy(
                                    errorMessage = "Rendering failed: ${status.error ?: "Unknown error"}"
                                )
                                saveCurrentState()
                                // Stop polling when failed
                                pollingJob?.cancel()
                            }
                            else -> {
                                // Continue polling for "queued" or "processing" status
                            }
                        }
                    }.onFailure { error ->
                        uiState = uiState.copy(
                            errorMessage = "Failed to get job status: ${error.message}"
                        )
                        saveCurrentState()
                    }
                } catch (e: Exception) {
                    uiState = uiState.copy(
                        errorMessage = "Error polling job status: ${e.message}"
                    )
                    saveCurrentState()
                }
                
                // Wait before polling again
                delay(3000) // Poll every 3 seconds
            }
        }
    }
    
    // Stop polling
    fun stopPolling() {
        pollingJob?.cancel()
        pollingJob = null
    }
    
    // Clear the current video
    fun clearVideo() {
        uiState = uiState.copy(
            videoUrl = null,
            currentJobId = null,
            currentJobStatus = null
        )
        saveCurrentState()
    }
    
    // Check server connection
    fun checkServerConnection() {
        viewModelScope.launch {
            try {
                val result = repository.getServerInfo()
                
                result.onSuccess {
                    uiState = uiState.copy(
                        isServerConnected = true,
                        errorMessage = null
                    )
                }.onFailure { error ->
                    uiState = uiState.copy(
                        isServerConnected = false,
                        errorMessage = "Cannot connect to server: ${error.message}"
                    )
                }
            } catch (e: Exception) {
                uiState = uiState.copy(
                    isServerConnected = false,
                    errorMessage = "Server connection error: ${e.message}"
                )
            }
        }
    }
    
    // Cancel the current job
    fun cancelJob() {
        pollingJob?.cancel()
        uiState = uiState.copy(
            isLoading = false,
            currentJobId = null,
            currentJobStatus = null
        )
        saveCurrentState()
    }
    
    // Clear error message
    fun clearError() {
        uiState = uiState.copy(errorMessage = null)
    }
    
    // UI State class
    data class UiState(
        val isLoading: Boolean = false,
        val errorMessage: String? = null,
        val startLocation: Location? = null,
        val selectedLocations: List<Location> = emptyList(),
        val selectedQuality: VideoQuality = VideoQuality.HD_1080P,
        val videoUrl: String? = null,
        val currentJobId: String? = null,
        val currentJobStatus: String? = null,
        val isServerConnected: Boolean = false
    )
    
    // Clean up on clearing ViewModel
    override fun onCleared() {
        super.onCleared()
        stopPolling()
        saveCurrentState()
    }
}
