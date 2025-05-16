package com.earthtour.client.data.api

import com.earthtour.client.data.models.AnimationRequest
import com.earthtour.client.data.models.AnimationResponse
import com.earthtour.client.data.models.JobStatus
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface EarthTourApi {
    
    @POST("/generate-animation")
    suspend fun generateAnimation(
        @Body request: AnimationRequest
    ): Response<AnimationResponse>
    
    @GET("/job/{jobId}")
    suspend fun getJobStatus(
        @Path("jobId") jobId: String
    ): Response<JobStatus>
    
    @GET("/")
    suspend fun getServerInfo(): Response<Map<String, String>>
}
