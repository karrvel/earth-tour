import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.models import AnimationRequest, AnimationResponse, Location, VideoQuality
from app.services.geocoder import geocoding_service
from app.services.renderer import blender_renderer
from app.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Earth Tour Server",
    description="Server for generating 3D flight path animations over Earth using Blender",
    version="1.0.0"
)

# TODO: tighten CORS settings before prod deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # super permissive for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create output directory if it doesn't exist
output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
os.makedirs(output_dir, exist_ok=True)

# Serve static files (videos)
app.mount("/videos", StaticFiles(directory=output_dir), name="videos")

# Job status tracking
animation_jobs = {}

@app.get("/")
async def root():
    """Root endpoint - returns basic server info"""
    return {
        "name": "Earth Tour Server",
        "version": "1.0.0",
        "status": "running"
    }

def process_animation_request(
    request_id: str,
    locations: List[Location],
    quality: VideoQuality,
    fps: int = 30,
    duration: Optional[int] = None
):
    """
    Background task to process animation requests.
    
    Args:
        request_id (str): Unique request ID
        locations (List[Location]): List of locations
        quality (VideoQuality): Video quality setting
        fps (int): Frames per second
        duration (int): Animation duration in seconds
    """
    try:
        animation_jobs[request_id]["status"] = "processing"
        
        # Process all locations to ensure we have coordinates
        processed_locations = []

        # This is a simple, but not the most efficient approach
        for location in locations:
            if location.lat is not None and location.lon is not None:
                # Location already has coordinates
                processed_locations.append((location.lat, location.lon))
            elif location.name:
                # Need to geocode the location
                coords = geocoding_service.geocode(location.name)
                if coords:
                    processed_locations.append(coords)
                else:
                    error_msg = f"Failed to geocode location: {location.name}"
                    logger.error(error_msg)
                    animation_jobs[request_id]["status"] = "failed"
                    animation_jobs[request_id]["error"] = error_msg
                    return
            else:
                error_msg = "Location missing both name and coordinates"
                logger.error(error_msg)
                animation_jobs[request_id]["status"] = "failed"
                animation_jobs[request_id]["error"] = error_msg
                return
        
        # Render the animation
        start_time = time.time()
        video_path = blender_renderer.render_animation(
            locations=processed_locations,
            quality=quality,
            fps=fps,
            duration=duration
        )
        render_time = time.time() - start_time
        
        if video_path:
            # Convert absolute path to URL path
            video_filename = os.path.basename(video_path)
            video_url = f"/videos/{video_filename}"
            
            # Update job status
            animation_jobs[request_id]["status"] = "completed"
            animation_jobs[request_id]["video_path"] = video_url
            animation_jobs[request_id]["duration"] = render_time
            
            logger.info(f"Animation completed: {video_path} in {render_time:.2f} seconds")
        else:
            # Handle rendering failure
            error_msg = "Failed to render animation"
            animation_jobs[request_id]["status"] = "failed"
            animation_jobs[request_id]["error"] = error_msg
            logger.error(error_msg)
            
    except Exception as e:
        error_msg = f"Error processing animation: {str(e)}"
        animation_jobs[request_id]["status"] = "failed"
        animation_jobs[request_id]["error"] = error_msg
        logger.error(error_msg)

@app.post("/generate-animation", response_model=dict)
async def generate_animation(request: AnimationRequest, background_tasks: BackgroundTasks):
    """
    Generate a flight path animation over Earth.
    
    Args:
        request (AnimationRequest): Animation request with locations and quality
        
    Returns:
        dict: Job ID and status information
    """
    try:
        # Validate request
        if len(request.locations) < 2:
            raise HTTPException(status_code=400, detail="At least 2 locations are required")
        
        # Generate a unique job ID
        request_id = f"job_{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(request)}"
        
        # Initialize job status
        animation_jobs[request_id] = {
            "id": request_id,
            "status": "queued",
            "created": datetime.now().isoformat(),
            "request": {
                "locations": [loc.dict() for loc in request.locations],
                "quality": request.quality.value
            }
        }
        
        # Add task to background processing
        background_tasks.add_task(
            process_animation_request,
            request_id,
            request.locations,
            request.quality,
            duration=request.duration
        )
        
        logger.info(f"Animation request queued with ID: {request_id}")
        
        # Return job information
        return {
            "job_id": request_id,
            "status": "queued",
            "message": "Animation request has been queued for processing"
        }
        
    except Exception as e:
        logger.error(f"Error processing animation request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of an animation job.
    
    Args:
        job_id (str): Job ID to check
        
    Returns:
        dict: Job status information
    """
    if job_id not in animation_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_info = animation_jobs[job_id]
    
    # If job is completed, include the video path
    if job_info["status"] == "completed":
        return {
            "job_id": job_id,
            "status": "completed",
            "video_path": job_info["video_path"],
            "duration": job_info["duration"]
        }
    
    # If job failed, include the error message
    elif job_info["status"] == "failed":
        return {
            "job_id": job_id,
            "status": "failed",
            "error": job_info.get("error", "Unknown error")
        }
    
    # Otherwise, just return the status
    else:
        return {
            "job_id": job_id,
            "status": job_info["status"]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
