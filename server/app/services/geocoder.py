import time
from functools import lru_cache
from typing import Dict, Tuple, Optional

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable

from app.utils.logger import get_logger

logger = get_logger(__name__)

class GeocodingService:
    def __init__(self, user_agent: str = "earth-tour-server"):
        """
        Initialize the geocoding service with Nominatim.
        
        Args:
            user_agent (str): User agent for Nominatim requests
        """
        self.geolocator = Nominatim(user_agent=user_agent)
        logger.info("Geocoding service initialized")
        
    @lru_cache(maxsize=1000)
    def geocode(self, location_name: str, max_retries: int = 3) -> Optional[Tuple[float, float]]:
        """
        Geocode a location name to latitude and longitude.
        
        Args:
            location_name (str): Name of the location to geocode
            max_retries (int): Maximum number of retries for geocoding
            
        Returns:
            Optional[Tuple[float, float]]: Tuple of (latitude, longitude) or None if geocoding failed
        """
        if not location_name:
            logger.error("Empty location name provided")
            return None
            
        retry_count = 0
        while retry_count < max_retries:
            try:
                logger.info(f"Geocoding location: {location_name}")
                location = self.geolocator.geocode(location_name)
                
                if location:
                    coords = (location.latitude, location.longitude)
                    logger.info(f"Geocoded {location_name} to {coords}")
                    return coords
                else:
                    logger.warning(f"Could not geocode location: {location_name}")
                    return None
                    
            except (GeocoderTimedOut, GeocoderUnavailable) as e:
                retry_count += 1
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.warning(f"Geocoding attempt {retry_count} failed: {str(e)}. Retrying in {wait_time}s.")
                time.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Unexpected error during geocoding: {str(e)}")
                return None
                
        logger.error(f"Failed to geocode {location_name} after {max_retries} attempts")
        return None

# Singleton instance
geocoding_service = GeocodingService()
