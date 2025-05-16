package com.earthtour.client.ui.components

import android.app.DownloadManager
import android.content.Context
import android.net.Uri
import android.os.Environment
import android.view.ViewGroup.LayoutParams.MATCH_PARENT
import android.widget.FrameLayout
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.composed
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.C
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.datasource.DefaultDataSource
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.exoplayer.source.ProgressiveMediaSource
import androidx.media3.ui.AspectRatioFrameLayout
import androidx.media3.ui.PlayerView
import com.earthtour.client.ui.theme.VideoBackground
import kotlinx.coroutines.delay
import java.io.File
import java.text.SimpleDateFormat
import java.util.*
import kotlin.math.floor

@androidx.annotation.OptIn(UnstableApi::class)
@Composable
fun VideoPlayer(
    videoUrl: String,
    onDownloadClick: () -> Unit = {}
) {
    val context = LocalContext.current
    
    // Create an ExoPlayer instance with better buffering and performance
    val exoPlayer = remember {
        ExoPlayer.Builder(context)
            .setLoadControl(
                androidx.media3.exoplayer.DefaultLoadControl.Builder()
                    .setBufferDurationsMs(
                        32 * 1024, // Min buffer duration
                        64 * 1024, // Max buffer duration
                        1024,    // Buffer for playback after rebuffer
                        1024     // Buffer for playback
                    )
                    .setPrioritizeTimeOverSizeThresholds(true)
                    .build()
            )
            .build().apply {
                val dataSourceFactory = DefaultDataSource.Factory(context)
                val mediaSource = ProgressiveMediaSource.Factory(dataSourceFactory)
                    .createMediaSource(MediaItem.fromUri(videoUrl))
                
                setMediaSource(mediaSource)
                prepare()
                playWhenReady = true
                repeatMode = Player.REPEAT_MODE_ALL
                videoScalingMode = C.VIDEO_SCALING_MODE_SCALE_TO_FIT_WITH_CROPPING
            }
    }
    
    // Track playback state
    var isPlaying by remember { mutableStateOf(true) }
    
    // Track buffering state
    var isBuffering by remember { mutableStateOf(false) }
    
    // Track current position and duration for seek bar
    var currentPosition by remember { mutableStateOf(0L) }
    var duration by remember { mutableStateOf(0L) }
    
    // Update position periodically
    LaunchedEffect(Unit) {
        while (true) {
            delay(500) // Update every half second
            currentPosition = exoPlayer.currentPosition
            duration = exoPlayer.duration.coerceAtLeast(0L)
            isPlaying = exoPlayer.isPlaying
            isBuffering = exoPlayer.playbackState == Player.STATE_BUFFERING
        }
    }
    
    // Clean up the ExoPlayer when the composable is disposed
    DisposableEffect(key1 = exoPlayer) {
        val listener = object : Player.Listener {
            override fun onIsPlayingChanged(isPlaying: Boolean) {
                super.onIsPlayingChanged(isPlaying)
            }
            
            override fun onPlaybackStateChanged(playbackState: Int) {
                super.onPlaybackStateChanged(playbackState)
                isBuffering = playbackState == Player.STATE_BUFFERING
            }
        }
        
        exoPlayer.addListener(listener)
        
        onDispose {
            exoPlayer.removeListener(listener)
            exoPlayer.release()
        }
    }
    
    // Video controls visibility
    var areControlsVisible by remember { mutableStateOf(true) }
    
    // Auto-hide controls
    LaunchedEffect(areControlsVisible) {
        if (areControlsVisible && isPlaying) {
            delay(3000)
            areControlsVisible = false
        }
    }
    
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(VideoBackground)
    ) {
        // Aspect ratio 9:16 for the video
        Box(
            modifier = Modifier
                .fillMaxSize()
                .align(Alignment.Center)
        ) {
            AndroidView(
                factory = { ctx ->
                    // Create a custom player view with better aspect ratio handling
                    PlayerView(ctx).apply {
                        player = exoPlayer
                        useController = false
                        resizeMode = AspectRatioFrameLayout.RESIZE_MODE_FILL

                        layoutParams = FrameLayout.LayoutParams(MATCH_PARENT, MATCH_PARENT)
                        
                        // Better handling of buffering states
                        setShowBuffering(PlayerView.SHOW_BUFFERING_ALWAYS)
                    }
                },
                modifier = Modifier.fillMaxSize()
            )
            
            // Buffering indicator
            if (isBuffering) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(Color.Black.copy(alpha = 0.3f)),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(
                        color = MaterialTheme.colorScheme.primary
                    )
                }
            }
        }
        
        // Show controls when visible
        AnimatedVisibility(
            visible = areControlsVisible,
            enter = fadeIn(),
            exit = fadeOut(),
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .fillMaxWidth()
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color.Black.copy(alpha = 0.7f))
                    .padding(8.dp)
            ) {
                // Seek bar
                Slider(
                    value = if (duration > 0) currentPosition.toFloat() / duration.toFloat() else 0f,
                    onValueChange = { progress ->
                        exoPlayer.seekTo((progress * duration).toLong())
                        currentPosition = (progress * duration).toLong()
                    },
                    colors = SliderDefaults.colors(
                        thumbColor = MaterialTheme.colorScheme.primary,
                        activeTrackColor = MaterialTheme.colorScheme.primary,
                        inactiveTrackColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.3f)
                    ),
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 8.dp)
                )
                
                // Time display and controls
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(8.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // Time display (current / total)
                    Text(
                        text = "${formatTime(currentPosition)} / ${formatTime(duration)}",
                        color = Color.White,
                        style = MaterialTheme.typography.bodySmall,
                        modifier = Modifier.width(90.dp)
                    )
                    
                    // Playback controls
                    Row(
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        // Rewind 10 seconds
                        IconButton(onClick = {
                            exoPlayer.seekTo((currentPosition - 10000).coerceAtLeast(0))
                        }) {
                            Icon(
                                imageVector = Icons.Filled.Replay10,
                                contentDescription = "Rewind 10 seconds",
                                tint = Color.White
                            )
                        }
                        
                        // Play/Pause
                        IconButton(onClick = {
                            if (exoPlayer.isPlaying) {
                                exoPlayer.pause()
                            } else {
                                exoPlayer.play()
                            }
                        }) {
                            Icon(
                                imageVector = if (exoPlayer.isPlaying) 
                                    Icons.Filled.Pause
                                else 
                                    Icons.Filled.PlayArrow,
                                contentDescription = "Play/Pause",
                                tint = Color.White,
                                modifier = Modifier.size(36.dp)
                            )
                        }
                        
                        // Forward 10 seconds
                        IconButton(onClick = {
                            exoPlayer.seekTo((currentPosition + 10000).coerceAtMost(duration))
                        }) {
                            Icon(
                                imageVector = Icons.Filled.Forward10,
                                contentDescription = "Forward 10 seconds",
                                tint = Color.White
                            )
                        }
                    }
                    
                    // Download button
                    IconButton(onClick = {
                        // Download the video
                        downloadVideo(context, videoUrl)
                        onDownloadClick()
                    }) {
                        Icon(
                            imageVector = Icons.Default.Download,
                            contentDescription = "Download",
                            tint = Color.White
                        )
                    }
                }
            }
        }
        
        // Touch to toggle controls
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(vertical = 60.dp) // Allow space for other UI elements
                .noRippleClickable { 
                    areControlsVisible = !areControlsVisible 
                }
        )
    }
}

// Format time in MM:SS format
private fun formatTime(timeMs: Long): String {
    if (timeMs <= 0) return "00:00"
    val totalSeconds = floor(timeMs / 1000.0).toInt()
    val minutes = totalSeconds / 60
    val seconds = totalSeconds % 60
    return "%02d:%02d".format(minutes, seconds)
}

// Extension function for no-ripple clickable
fun Modifier.noRippleClickable(onClick: () -> Unit): Modifier = composed {
    clickable(
        interactionSource = remember { MutableInteractionSource() },
        indication = null,
        onClick = onClick
    )
}

// Function to download the video
private fun downloadVideo(context: Context, videoUrl: String) {
    try {
        // Extract meaningful information from the video URL
        val videoFileName = Uri.parse(videoUrl).lastPathSegment ?: "video"
        
        // Extract any location information from filename (if server includes this)
        val locationInfo = if (videoFileName.contains("_")) {
            videoFileName.substringBefore(".").replace("_", "-")
        } else {
            "tour"
        }
        
        // Add timestamp to ensure uniqueness
        val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
        
        // Create a unique identifier based on videoURL hash
        val urlHash = videoUrl.hashCode().toString().takeLast(6)
        
        // Combine all elements for a highly unique filename
        val fileName = "EarthTour_${locationInfo}_${timestamp}_${urlHash}.mp4"
        
        val downloadManager = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
        val uri = Uri.parse(videoUrl)
        
        val request = DownloadManager.Request(uri).apply {
            setTitle("Earth Tour Video")
            setDescription("Downloading Earth Tour video")
            setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
            setDestinationInExternalPublicDir(Environment.DIRECTORY_MOVIES, fileName)
        }
        
        downloadManager.enqueue(request)
    } catch (e: Exception) {
        e.printStackTrace()
        // You might want to show a toast or other notification here
    }
}
