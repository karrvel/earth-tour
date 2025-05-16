# Earth Tour

Earth Tour is a full-stack application that generates amazing 3D flight path animations over a realistic Earth model. The system consists of a Python backend server that uses Blender for rendering and a Kotlin Android client app.

## Project Structure

The project is divided into two main components:

- **`/client`**: An Android app built with Kotlin and Jetpack Compose
- **`/server`**: A Python FastAPI server that processes animation requests and uses Blender for rendering

## How It Works

1. The Android app allows users to select multiple locations (cities or coordinates)
2. The app sends these locations along with rendering preferences to the server
3. The server geocodes city names to coordinates using GeoPy
4. Blender is invoked to generate a 3D animation traveling between the specified points
5. The rendered video is made available to the client for streaming or download

## Key Features

- Beautiful 3D animations following great-circle paths between locations
- Multiple waypoint support with smooth camera transitions
- Configurable video quality (720p to 4K)
- Real-time rendering status updates
- Popular location presets and custom coordinate input

## Setup and Installation

### Server Setup

1. Navigate to the server directory:
   ```
   cd server
   ```

2. Install the required Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Make sure Blender 3.3+ is installed and accessible from the command line

4. Start the server:
   ```
   uvicorn app.main:app --reload
   ```

### Client Setup

1. Open the client project in Android Studio

2. Modify the API base URL in the client code if needed (default is http://10.0.2.2:8000 for emulator)

3. Build and run the application on an emulator or physical device

## Technical Details

The system architecture follows a client-server model:

- The server exposes a REST API built with FastAPI
- Animations are rendered asynchronously with job status tracking
- The client follows MVVM architecture with Jetpack Compose for UI

## Requirements

- Python 3.9+
- Blender 3.3+
- Android Studio Electric Eel (2022.1.1) or newer
- JDK 17
- Android SDK 34

## Future Improvements

- Add user accounts and saved animation history
- Implement more camera path options and effects
- Add support for custom 3D models at waypoints
- Create a web client version

## License

This project is distributed under the MIT License.
