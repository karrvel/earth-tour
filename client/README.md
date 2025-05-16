# Earth Tour Client

A beautiful Kotlin Android application that interacts with the Earth Tour Server to generate and view 3D flight path animations over Earth.

## Features

- Beautiful 9:16 video player for Earth tour animations
- Settings panel for configuring tour parameters:
  - Start location selection
  - Multiple destination locations
  - Video quality options (720p, 1080p, 1440p, 4K)
- Video download functionality
- Real-time rendering status updates
- Pre-defined popular locations
- Custom location input (by name or coordinates)

## Requirements

- Android Studio Electric Eel (2022.1.1) or newer
- JDK 17
- Android SDK 34
- Earth Tour Server running on localhost:8000 (or adjust the API base URL)

## Setup

1. Clone this repository
2. Open the project in Android Studio
3. Make sure the Earth Tour Server is running (default URL is http://10.0.2.2:8000 for emulator)
4. Build and run the application

## Architecture

The application follows the MVVM (Model-View-ViewModel) architecture pattern:

- **Model**: Data classes and repository for communication with the Earth Tour Server
- **View**: Jetpack Compose UI components
- **ViewModel**: MainViewModel class to manage UI state and business logic

## API Integration

The app integrates with these endpoints from the Earth Tour Server:
- `POST /generate-animation` - Request a new animation
- `GET /job/{jobId}` - Check the status of an animation job
- `GET /videos/{videoFileName}` - Stream the rendered video

## Technology Stack

- [Kotlin](https://kotlinlang.org/) - Programming language
- [Jetpack Compose](https://developer.android.com/jetpack/compose) - Modern UI toolkit
- [Media3/ExoPlayer](https://developer.android.com/media/media3) - Video playback
- [Retrofit](https://square.github.io/retrofit/) - HTTP client for API communication
- [Coroutines](https://kotlinlang.org/docs/coroutines-overview.html) - Asynchronous programming
- [Material3](https://m3.material.io/) - Design system

## Customization

To customize the application:
- Update the API base URL in `ApiClient.kt` if your server is running on a different address
- Modify the `PredefinedLocations` object in `Models.kt` to change the list of popular locations
