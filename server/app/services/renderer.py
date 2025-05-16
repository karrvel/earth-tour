import os
import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

from app.utils.logger import get_logger
from app.models import Location, VideoQuality

logger = get_logger(__name__)

class BlenderRenderer:
    def __init__(self, blender_path: str = "/Applications/Blender.app/Contents/MacOS/Blender", 
                 script_path: str = None,
                 output_dir: str = None):
        """
        Initialize the Blender renderer.
        
        Args:
            blender_path (str): Path to the Blender executable
            script_path (str): Path to the Blender Python script
            output_dir (str): Directory to save rendered videos
        """
        self.blender_path = blender_path
        
        # Use default script path if not provided
        if script_path is None:
            base_dir = Path(__file__).parent.parent.parent
            self.script_path = str(base_dir / "blender_scripts" / "render_flight_simple.py")
        else:
            self.script_path = script_path
            
        # Use default output directory if not provided
        if output_dir is None:
            base_dir = Path(__file__).parent.parent.parent
            self.output_dir = str(base_dir / "output")
        else:
            self.output_dir = output_dir
            
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create a directory for config files if it doesn't exist
        self.config_dir = str(Path(self.output_dir).parent / "config")
        os.makedirs(self.config_dir, exist_ok=True)
        
        logger.info(f"Blender renderer initialized with script: {self.script_path}")
        logger.info(f"Output directory set to: {self.output_dir}")
        logger.info(f"Config directory set to: {self.config_dir}")
    
    def _prepare_config(self, locations: List[Tuple[float, float]], 
                        quality: VideoQuality,
                        fps: int = 30,
                        duration: int = 10) -> str:
        """
        Prepare configuration file for Blender script.
        
        Args:
            locations (List[Tuple[float, float]]): List of (lat, lon) tuples
            quality (VideoQuality): Video quality enum
            fps (int): Frames per second
            duration (int): Animation duration in seconds
            
        Returns:
            str: Path to the configuration file
        """
        # Prepare the configuration data
        config_data = {
            "locations": [{"lat": lat, "lon": lon} for lat, lon in locations],
            "quality": quality.value,
            "fps": fps,
            "duration": duration
        }
        
        # Create a timestamp-based filename for the config
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_filename = f"earth_tour_config_{timestamp}.json"
        config_path = os.path.join(self.config_dir, config_filename)
        
        # Write the configuration to a file
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
            
        logger.info(f"Created configuration file: {config_path}")
        return config_path
    
    def _generate_output_filename(self, quality: VideoQuality) -> str:
        """
        Generate a unique output filename based on timestamp and quality.
        
        Args:
            quality (VideoQuality): Video quality setting
            
        Returns:
            str: Path to the output video file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"earth_tour_{timestamp}_{quality.value}.mp4"
        output_path = os.path.join(self.output_dir, filename)
        
        logger.info(f"Generated output filename: {output_path}")
        return output_path
    
    def render_animation(self, locations: List[Tuple[float, float]], 
                         quality: VideoQuality,
                         fps: int = 30,
                         duration: int = None) -> Optional[str]:
        """
        Render a flight path animation using Blender.
        
        Args:
            locations (List[Tuple[float, float]]): List of (lat, lon) tuples
            quality (VideoQuality): Video quality enum
            fps (int): Frames per second
            duration (int, optional): Animation duration in seconds. If None, duration will be calculated based on the number of locations.
            
        Returns:
            Optional[str]: Path to the rendered video file or None if rendering failed
        """
        if not locations or len(locations) < 2:
            logger.error("At least 2 locations are required for animation")
            return None
        
        # Calculate dynamic duration if not provided
        if duration is None:
            # Base duration: 5 seconds for 2 locations, +3 seconds for each additional location
            num_locations = len(locations)
            duration = 5 + (num_locations - 2) * 3
            logger.info(f"Calculated dynamic duration: {duration}s for {num_locations} locations")
            
        try:
            # Prepare configuration file
            config_path = self._prepare_config(locations, quality, fps, duration)
            
            # Generate output path
            output_path = self._generate_output_filename(quality)
            
            # Build Blender command
            blender_cmd = [
                self.blender_path,
                "--background",
                "--python", self.script_path,
                "--",
                "--config", config_path,
                "--output", output_path
            ]
            
            logger.info(f"Executing Blender: {' '.join(blender_cmd)}")
            
            # Run Blender process
            process = subprocess.Popen(
                blender_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Capture output
            stdout, stderr = process.communicate()
            
            # Check if rendering was successful
            if process.returncode != 0:
                logger.error(f"Blender rendering failed with code {process.returncode}")
                logger.error(f"Stderr: {stderr}")
                logger.debug(f"Stdout: {stdout}")
                return None
                
            logger.info(f"Blender rendering completed successfully")
            logger.debug(f"Blender stdout: {stdout}")
            
            # Clean up config file (optional)
            # We're keeping it for now for debugging purposes
            # try:
            #     os.remove(config_path)
            # except Exception as e:
            #     logger.warning(f"Failed to clean up config file: {str(e)}")
                
            # Check if output file exists
            if os.path.exists(output_path):
                return output_path
            else:
                logger.error(f"Output file not found: {output_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error during rendering: {str(e)}")
            return None

# Singleton instance
blender_renderer = BlenderRenderer()
