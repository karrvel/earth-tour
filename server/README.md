# Earth Tour Server

A Python-based server-side application that generates 3D flight path animations over a realistic Earth model using Blender.

## Features

- FastAPI server with endpoints for flight path animation generation
- Geocode city names to coordinates using GeoPy
- Generate 3D animations using Blender's Python API in headless mode
- Support for multiple waypoints with great-circle interpolation
- Customizable video quality settings (720p, 1080p, 1440p, 4K)

## Requirements

- Python 3.9+
- Blender 3.3+ (installed and accessible via command line)
- Dependencies listed in `requirements.txt`

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Ensure Blender is installed and accessible in your PATH

## Usage

1. Start the server:
   ```
   uvicorn app.main:app --reload
   ```
2. Access the API documentation at http://localhost:8000/docs
3. Send a POST request to `/generate-animation` with:
   - List of locations (city names or lat/long coordinates)
   - Video quality setting

## API Endpoints

### POST /generate-animation

Generate a flight path animation over Earth.

Request body:
```json
{
  "locations": [
    {"name": "New York"},
    {"lat": 48.8566, "lon": 2.3522},
    {"name": "Tokyo"}
  ],
  "quality": "1080p"
}
```

Response:
```json
{
  "video_path": "/path/to/rendered/video.mp4",
  "duration": 15.5
}
```
