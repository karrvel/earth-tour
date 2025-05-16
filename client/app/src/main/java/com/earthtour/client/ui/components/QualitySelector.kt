package com.earthtour.client.ui.components

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.earthtour.client.data.models.VideoQuality

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun QualitySelector(
    selectedQuality: VideoQuality,
    onQualitySelected: (VideoQuality) -> Unit
) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            VideoQuality.values().forEach { quality ->
                FilterChip(
                    selected = quality == selectedQuality,
                    onClick = { onQualitySelected(quality) },
                    label = { 
                        Text(
                            text = when(quality) {
                                VideoQuality.HD_720P -> "720p"
                                VideoQuality.HD_1080P -> "1080p"
                                VideoQuality.QHD_1440P -> "1440p"
                                VideoQuality.UHD_4K -> "4K"
                            }
                        ) 
                    },
                    shape = RoundedCornerShape(8.dp)
                )
            }
        }
    }
}
