package com.earthtour.client.ui.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.earthtour.client.data.models.Location
import com.earthtour.client.data.models.PredefinedLocations

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LocationSelector(
    selectedLocation: Location?,
    onLocationSelected: (Location) -> Unit,
    label: String = "Select Location"
) {
    var showDialog by remember { mutableStateOf(false) }
    var useCustomLocation by remember { mutableStateOf(false) }
    var customLocationName by remember { mutableStateOf("") }
    var customLatitude by remember { mutableStateOf("") }
    var customLongitude by remember { mutableStateOf("") }
    
    // Show the selected location or a placeholder
    OutlinedCard(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { showDialog = true },
        shape = RoundedCornerShape(8.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = Icons.Default.LocationOn,
                contentDescription = "Location",
                tint = MaterialTheme.colorScheme.primary
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = selectedLocation?.name 
                    ?: selectedLocation?.let { "Lat: ${it.lat}, Lon: ${it.lon}" }
                    ?: label,
                style = MaterialTheme.typography.bodyLarge,
                color = if (selectedLocation == null) 
                    MaterialTheme.colorScheme.onSurface.copy(alpha = 0.6f)
                else 
                    MaterialTheme.colorScheme.onSurface
            )
        }
    }
    
    // Location selection dialog
    if (showDialog) {
        AlertDialog(
            onDismissRequest = { showDialog = false },
            title = { Text("Select Location") },
            text = {
                Column(modifier = Modifier.fillMaxWidth()) {
                    // Toggle between predefined and custom locations
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.Center
                    ) {
                        FilterChip(
                            selected = !useCustomLocation,
                            onClick = { useCustomLocation = false },
                            label = { Text("Popular Locations") },
                            modifier = Modifier
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        FilterChip(
                            selected = useCustomLocation,
                            onClick = { useCustomLocation = true },
                            label = { Text("Custom Location") },
                            modifier = Modifier
                        )
                    }
                    
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    if (useCustomLocation) {
                        // Custom location input
                        OutlinedTextField(
                            value = customLocationName,
                            onValueChange = { customLocationName = it },
                            label = { Text("Location Name (optional)") },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true
                        )
                        
                        Spacer(modifier = Modifier.height(8.dp))
                        
                        OutlinedTextField(
                            value = customLatitude,
                            onValueChange = { customLatitude = it },
                            label = { Text("Latitude") },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true
                        )
                        
                        Spacer(modifier = Modifier.height(8.dp))
                        
                        OutlinedTextField(
                            value = customLongitude,
                            onValueChange = { customLongitude = it },
                            label = { Text("Longitude") },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true
                        )
                    } else {
                        // Predefined locations list
                        PredefinedLocations.LOCATIONS.forEach { location ->
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clickable { 
                                        onLocationSelected(location)
                                        showDialog = false
                                    }
                                    .padding(vertical = 8.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Icon(
                                    imageVector = Icons.Default.LocationOn,
                                    contentDescription = null,
                                    tint = MaterialTheme.colorScheme.primary
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(location.name ?: "")
                            }
                            Divider()
                        }
                    }
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        if (useCustomLocation) {
                            // Validate and create custom location
                            val lat = customLatitude.toDoubleOrNull()
                            val lon = customLongitude.toDoubleOrNull()
                            
                            if ((lat != null && lon != null) || customLocationName.isNotBlank()) {
                                val location = Location(
                                    name = if (customLocationName.isNotBlank()) customLocationName else null,
                                    lat = lat,
                                    lon = lon
                                )
                                onLocationSelected(location)
                                showDialog = false
                            }
                        }
                    },
                    enabled = if (useCustomLocation) {
                        (customLatitude.toDoubleOrNull() != null && 
                         customLongitude.toDoubleOrNull() != null) || 
                        customLocationName.isNotBlank()
                    } else true
                ) {
                    Text("Confirm")
                }
            },
            dismissButton = {
                TextButton(onClick = { showDialog = false }) {
                    Text("Cancel")
                }
            }
        )
    }
}
