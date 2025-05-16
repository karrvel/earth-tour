from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator


class VideoQuality(str, Enum):
    HD_720P = "720p"
    HD_1080P = "1080p"
    QHD_1440P = "1440p"
    UHD_4K = "4K"


class LocationByName(BaseModel):
    name: str = Field(..., description="City or location name")
    
    
class LocationByCoordinates(BaseModel):
    lat: float = Field(..., description="Latitude in decimal degrees", ge=-90, le=90)
    lon: float = Field(..., description="Longitude in decimal degrees", ge=-180, le=180)


class Location(BaseModel):
    name: Optional[str] = Field(None, description="City or location name")
    lat: Optional[float] = Field(None, description="Latitude in decimal degrees", ge=-90, le=90)
    lon: Optional[float] = Field(None, description="Longitude in decimal degrees", ge=-180, le=180)
    
    @validator('lat')
    def validate_lat_lon_pair(cls, v, values):
        # If lat is provided, lon must also be provided
        if v is not None and 'lon' not in values:
            raise ValueError("If latitude is provided, longitude must also be provided")
        return v
    
    @validator('name')
    def validate_name_or_coordinates(cls, v, values):
        # Either name or both lat/lon must be provided
        if v is None and ('lat' not in values or values.get('lat') is None):
            raise ValueError("Either name or both lat/lon must be provided")
        return v


class AnimationRequest(BaseModel):
    locations: List[Location] = Field(..., min_items=2, description="List of locations (min 2)")
    quality: VideoQuality = Field(VideoQuality.HD_1080P, description="Video quality setting")
    duration: Optional[int] = Field(None, description="Animation duration in seconds (optional, dynamically calculated if not provided)")
    
    @validator('locations')
    def validate_locations(cls, v):
        if len(v) < 2:
            raise ValueError("At least 2 locations are required")
        return v


class AnimationResponse(BaseModel):
    video_path: str = Field(..., description="Path to the rendered video file")
    duration: float = Field(..., description="Duration of the animation in seconds")
