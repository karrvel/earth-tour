package com.earthtour.client.ui.screens

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.earthtour.client.ui.components.LocationSelector
import com.earthtour.client.ui.components.QualitySelector
import com.earthtour.client.ui.components.VideoPlayer
import com.earthtour.client.ui.theme.VideoBackground
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

@Composable
fun MainScreen(
    viewModel: MainViewModel = viewModel()
) {
    val uiState = viewModel.uiState
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    
    // Track whether controls panel is expanded or collapsed
    var isPanelExpanded by remember { mutableStateOf(true) }
    
    // Auto-collapse when video loads
    LaunchedEffect(uiState.videoUrl) {
        if (uiState.videoUrl != null) {
            // Allow a short delay for the video to start displaying before collapsing
            delay(500)
            isPanelExpanded = false
        }
    }
    
    // Check server connection when the screen is first composed
    LaunchedEffect(Unit) {
        viewModel.checkServerConnection()
    }
    
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
    ) {
        Column(
            modifier = Modifier.fillMaxSize()
        ) {
            // Video player section (9:16 aspect ratio)
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .background(VideoBackground),
                contentAlignment = Alignment.Center
            ) {
                if (uiState.videoUrl != null) {
                    // Show video player when we have a video URL
                    VideoPlayer(
                        videoUrl = uiState.videoUrl,
                        onDownloadClick = {
                            // Handle download action (implemented in VideoPlayer component)
                        }
                    )
                } else if (uiState.isLoading || uiState.currentJobStatus != null) {
                    // Show loading indicator when loading or when a job is in progress
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        CircularProgressIndicator(
                            color = MaterialTheme.colorScheme.primary
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            text = "Generating your Earth tour...",
                            style = MaterialTheme.typography.bodyLarge,
                            color = Color.White
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = if (uiState.currentJobStatus == "processing") 
                                "Processing animation (this may take a few minutes)" 
                            else "Request queued",
                            style = MaterialTheme.typography.bodyMedium,
                            color = Color.White.copy(alpha = 0.7f)
                        )
                    }
                } else {
                    // Show placeholder
                    Text(
                        text = "Select locations and press 'Render' to generate your Earth tour",
                        style = MaterialTheme.typography.bodyLarge,
                        color = Color.White,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.padding(32.dp)
                    )
                }
            }
            
            // Pull-up handle (only visible when panel is collapsed and video is loaded)
            AnimatedVisibility(
                visible = !isPanelExpanded && uiState.videoUrl != null,
                enter = fadeIn() + slideInVertically(),
                exit = fadeOut() + slideOutVertically()
            ) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(32.dp)
                        .background(MaterialTheme.colorScheme.surfaceVariant)
                        .pointerInput(Unit) {
                            detectVerticalDragGestures { _, dragAmount ->
                                if (dragAmount < -5) { // Upward swipe
                                    coroutineScope.launch {
                                        isPanelExpanded = true
                                    }
                                }
                            }
                        }
                        .clickable { isPanelExpanded = true },
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.KeyboardArrowUp,
                        contentDescription = "Show controls",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            
            // Settings section with animation
            AnimatedVisibility(
                visible = isPanelExpanded,
                enter = expandVertically(
                    animationSpec = spring(
                        dampingRatio = Spring.DampingRatioMediumBouncy,
                        stiffness = Spring.StiffnessMedium
                    )
                ),
                exit = shrinkVertically(
                    animationSpec = tween(
                        durationMillis = 300,
                        easing = FastOutSlowInEasing
                    )
                )
            ) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp)
                        .pointerInput(Unit) {
                            detectVerticalDragGestures { _, dragAmount ->
                                if (dragAmount > 5 && uiState.videoUrl != null) { // Downward swipe
                                    coroutineScope.launch {
                                        isPanelExpanded = false
                                    }
                                }
                            }
                        },
                    shape = RoundedCornerShape(16.dp),
                    elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp)
                            .verticalScroll(rememberScrollState())
                    ) {
                        // Collapse handle indicator (only when video is showing)
                        if (uiState.videoUrl != null) {
                            Box(
                                modifier = Modifier
                                    .width(40.dp)
                                    .height(4.dp)
                                    .background(
                                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.3f),
                                        shape = RoundedCornerShape(2.dp)
                                    )
                                    .align(Alignment.CenterHorizontally)
                            )
                            Spacer(modifier = Modifier.height(16.dp))
                        }
                        
                        // Server connection status
                        if (!uiState.isServerConnected) {
                            Surface(
                                color = MaterialTheme.colorScheme.errorContainer,
                                shape = RoundedCornerShape(8.dp),
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(bottom = 16.dp)
                            ) {
                                Row(
                                    modifier = Modifier.padding(8.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.Warning,
                                        contentDescription = "Warning",
                                        tint = MaterialTheme.colorScheme.error
                                    )
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text(
                                        text = "Cannot connect to Earth Tour server",
                                        color = MaterialTheme.colorScheme.error
                                    )
                                }
                            }
                        }
                        
                        // Error message
                        if (uiState.errorMessage != null) {
                            Surface(
                                color = MaterialTheme.colorScheme.errorContainer,
                                shape = RoundedCornerShape(8.dp),
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(bottom = 16.dp)
                            ) {
                                Row(
                                    modifier = Modifier.padding(8.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.Warning,
                                        contentDescription = "Error",
                                        tint = MaterialTheme.colorScheme.error
                                    )
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text(
                                        text = uiState.errorMessage,
                                        color = MaterialTheme.colorScheme.error
                                    )
                                }
                            }
                        }
                        
                        // Start location selector
                        Text(
                            text = "Start Location",
                            style = MaterialTheme.typography.titleMedium
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        LocationSelector(
                            selectedLocation = uiState.startLocation,
                            onLocationSelected = { viewModel.updateStartLocation(it) }
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        
                        // Additional locations
                        Text(
                            text = "Tour Destinations",
                            style = MaterialTheme.typography.titleMedium
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        
                        // Selected locations list
                        Column {
                            uiState.selectedLocations.forEachIndexed { index, location ->
                                key(index) {
                                    Row(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(vertical = 4.dp),
                                        verticalAlignment = Alignment.CenterVertically
                                    ) {
                                        Text(
                                            text = location.name ?: "Lat: ${location.lat}, Lon: ${location.lon}",
                                            modifier = Modifier.weight(1f)
                                        )
                                        TextButton(
                                            onClick = { viewModel.removeLocation(location) }
                                        ) {
                                            Text("Remove")
                                        }
                                    }
                                    Divider()
                                }
                            }
                        }
                        
                        // Add new location
                        Spacer(modifier = Modifier.height(8.dp))
                        LocationSelector(
                            selectedLocation = null,
                            onLocationSelected = { viewModel.addLocation(it) },
                            label = "Add Destination"
                        )
                        
                        Spacer(modifier = Modifier.height(16.dp))
                        
                        // Video quality selector
                        Text(
                            text = "Video Quality",
                            style = MaterialTheme.typography.titleMedium
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        QualitySelector(
                            selectedQuality = uiState.selectedQuality,
                            onQualitySelected = { viewModel.updateVideoQuality(it) }
                        )
                        
                        Spacer(modifier = Modifier.height(24.dp))
                        
                        // Render button
                        Button(
                            onClick = { viewModel.generateAnimation() },
                            modifier = Modifier.fillMaxWidth(),
                            enabled = (uiState.startLocation != null || uiState.selectedLocations.isNotEmpty()) 
                                    && !uiState.isLoading
                                    && uiState.isServerConnected
                        ) {
                            Text("Render Tour")
                        }
                        
                        // Clear video button (only show if we have a video)
                        if (uiState.videoUrl != null) {
                            Spacer(modifier = Modifier.height(8.dp))
                            OutlinedButton(
                                onClick = { viewModel.clearVideo() },
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text("Create New Tour")
                            }
                        }
                    }
                }
            }
        }
    }
}
