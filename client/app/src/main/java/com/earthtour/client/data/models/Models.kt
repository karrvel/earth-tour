package com.earthtour.client.data.models

import com.google.gson.annotations.SerializedName

enum class VideoQuality(val value: String) {
    @SerializedName("720p")
    HD_720P("720p"),
    
    @SerializedName("1080p")
    HD_1080P("1080p"),
    
    @SerializedName("1440p")
    QHD_1440P("1440p"),
    
    @SerializedName("4K")
    UHD_4K("4K")
}

data class Location(
    val name: String? = null,
    val lat: Double? = null,
    val lon: Double? = null
) {
    // Validation function to ensure either name or both lat/lon are provided
    fun isValid(): Boolean {
        return (name != null) || (lat != null && lon != null)
    }
}

data class AnimationRequest(
    val locations: List<Location>,
    val quality: VideoQuality = VideoQuality.HD_1080P,
    val duration: Int? = null
)

data class AnimationResponse(
    val job_id: String,
    val status: String,
    val message: String
)

data class JobStatus(
    val id: String,
    val status: String,
    val created: String,
    val video_path: String? = null,
    val duration: Double? = null,
    val error: String? = null,
    val request: RequestInfo? = null
)

data class RequestInfo(
    val locations: List<Location>,
    val quality: String
)

// Predefined list of popular locations around the world
object PredefinedLocations {
    val LOCATIONS = listOf(
        Location(name = "Beijing, China"),
        Location(name = "Cairo, Egypt"),
        Location(name = "Cape Town, South Africa"),
        Location(name = "Dubai, UAE"),
        Location(name = "Istanbul, Turkey"),
        Location(name = "London, UK"),
        Location(name = "Moscow, Russia"),
        Location(name = "Mumbai, India"),
        Location(name = "New York, USA"),
        Location(name = "Paris, France"),
        Location(name = "Rio de Janeiro, Brazil"),
        Location(name = "Rome, Italy"),
        Location(name = "San Francisco, USA"),
        Location(name = "Sydney, Australia"),
        Location(name = "Tashkent, Uzbekistan"),
        Location(name = "Tokyo, Japan")
    )
}
