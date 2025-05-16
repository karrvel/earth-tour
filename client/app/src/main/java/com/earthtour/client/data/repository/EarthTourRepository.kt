package com.earthtour.client.data.repository

import com.earthtour.client.data.api.ApiClient
import com.earthtour.client.data.api.EarthTourApi
import com.earthtour.client.data.models.AnimationRequest
import com.earthtour.client.data.models.AnimationResponse
import com.earthtour.client.data.models.JobStatus
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import retrofit2.Response

class EarthTourRepository {
    private val api: EarthTourApi = ApiClient.earthTourApi
    
    suspend fun generateAnimation(request: AnimationRequest): Result<AnimationResponse> {
        return withContext(Dispatchers.IO) {
            try {
                val response = api.generateAnimation(request)
                if (response.isSuccessful) {
                    response.body()?.let {
                        Result.success(it)
                    } ?: Result.failure(Exception("Response body is null"))
                } else {
                    Result.failure(Exception("Error: ${response.code()} - ${response.message()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    suspend fun getJobStatus(jobId: String): Result<JobStatus> {
        return withContext(Dispatchers.IO) {
            try {
                val response = api.getJobStatus(jobId)
                if (response.isSuccessful) {
                    response.body()?.let {
                        Result.success(it)
                    } ?: Result.failure(Exception("Response body is null"))
                } else {
                    Result.failure(Exception("Error: ${response.code()} - ${response.message()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
    
    suspend fun getServerInfo(): Result<Map<String, String>> {
        return withContext(Dispatchers.IO) {
            try {
                val response = api.getServerInfo()
                if (response.isSuccessful) {
                    response.body()?.let {
                        Result.success(it)
                    } ?: Result.failure(Exception("Response body is null"))
                } else {
                    Result.failure(Exception("Error: ${response.code()} - ${response.message()}"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
}
