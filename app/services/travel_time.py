import os
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TravelTimeService:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    
    def calculate_travel_times(self, origin: str, destination: str, use_tuesday: bool = False, day_offset: int = 0) -> Dict[str, Optional[float]]:
        """
        Calculate travel times for all time slots.
        
        Args:
            origin: Origin address
            destination: Destination address
            use_tuesday: If True, use Tuesday instead of Monday (default: False)
            day_offset: Days to add/subtract from the target date (default: 0)
            
        Returns:
            Dictionary with travel times and display formats
        """
        if not origin or not destination:
            raise ValueError("Origin and destination must be provided")
            
        if not self.api_key:
            logger.warning("Google Maps API key not found. Using fallback calculation.")
            return self._fallback_calculation(origin, destination)
        
        travel_times = {}
        time_slots = {
            'travel_time_830am': self._get_departure_time(8, 30, day_offset, use_tuesday),
            'travel_time_930am': self._get_departure_time(9, 30, day_offset, use_tuesday),
            'travel_time_midday': self._get_departure_time(12, 0, day_offset, use_tuesday),
            'travel_time_630pm': self._get_departure_time(18, 30, day_offset, use_tuesday),
            'travel_time_730pm': self._get_departure_time(19, 30, day_offset, use_tuesday)
        }
        
        # For anomaly detection
        all_times = []
        anomaly_detected = False
        
        # First pass - calculate all times
        for time_key, departure_time in time_slots.items():
            try:
                travel_time_data = self._get_travel_time(origin, destination, departure_time)
                if travel_time_data:
                    # Store the conservative (max) time for database storage
                    travel_times[time_key] = travel_time_data['conservative']
                    # Also store the display format for frontend
                    travel_times[f"{time_key}_display"] = travel_time_data['display']
                    # Store for anomaly detection
                    all_times.append(travel_time_data['conservative'])
                else:
                    travel_times[time_key] = None
            except Exception as e:
                logger.error(f"Error calculating travel time for {time_key}: {e}")
                travel_times[time_key] = None
                anomaly_detected = True
        
        # Check for anomalies if we have enough data
        if len(all_times) >= 3 and not anomaly_detected:
            median_time = sorted(all_times)[len(all_times) // 2]
            
            # Check for extreme outliers (more than 2x the median)
            for time_key in ['travel_time_830am', 'travel_time_930am']:
                if time_key in travel_times and travel_times[time_key] is not None:
                    if travel_times[time_key] > 2 * median_time:
                        logger.warning(f"Anomaly detected in {time_key}: {travel_times[time_key]} > 2 * {median_time}")
                        travel_times[f"{time_key}_anomaly"] = True
                        
                        # If this is the first attempt, try with Tuesday
                        if not use_tuesday and day_offset == 0:
                            travel_times[f"{time_key}_note"] = "Unusually high traffic detected - possibly an incident"
        
        # Add metadata about the calculation
        day_name = "Tuesday" if use_tuesday else "Monday"
        if day_offset < 0:
            day_name = f"past {day_name} ({abs(day_offset)} days ago)"
        elif day_offset > 0:
            day_name = f"future {day_name} ({day_offset} days ahead)"
        else:
            day_name = f"next {day_name}"
            
        travel_times['calculation_day'] = day_name
        travel_times['calculation_timestamp'] = int(datetime.now().timestamp())
        
        return travel_times
    
    def _get_departure_time(self, hour: int, minute: int, day_offset: int = 0, use_tuesday: bool = False) -> int:
        """Get departure time as Unix timestamp for next Monday (or Tuesday) at specified time.
        
        Args:
            hour: Hour of the day (24-hour format)
            minute: Minute of the hour
            day_offset: Days to add/subtract from the target date (default: 0)
            use_tuesday: If True, use Tuesday instead of Monday (default: False)
        """
        now = datetime.now()
        
        # Calculate for next Monday (0) or Tuesday (1)
        target_weekday = 1 if use_tuesday else 0
        days_ahead = (target_weekday - now.weekday()) % 7
        if days_ahead == 0:  # If today is the target day, use next week
            days_ahead = 7
        
        target_date = now + timedelta(days=days_ahead + day_offset)
        departure_time = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return int(departure_time.timestamp())
    
    def _get_travel_time(self, origin: str, destination: str, departure_time: int) -> Optional[dict]:
        """Get travel time from Google Maps API for specific departure time.
        Returns dict with 'min', 'max', and 'typical' times in minutes.
        """
        params = {
            'origins': origin,
            'destinations': destination,
            'departure_time': departure_time,
            'traffic_model': 'best_guess',
            'mode': 'driving',
            'key': self.api_key
        }
        
        response = requests.get(self.base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] != 'OK':
            raise Exception(f"Google Maps API error: {data['status']}")
        
        rows = data.get('rows', [])
        if not rows or not rows[0].get('elements'):
            raise Exception("No route found")
        
        element = rows[0]['elements'][0]
        if element['status'] != 'OK':
            raise Exception(f"Route calculation error: {element['status']}")
        
        # Get duration in traffic (more accurate) or regular duration
        duration_in_traffic = element.get('duration_in_traffic')
        duration_normal = element.get('duration')
        
        if not duration_in_traffic and not duration_normal:
            raise Exception("No duration data available")
        
        # Convert seconds to minutes
        if duration_in_traffic:
            typical_time = round(duration_in_traffic['value'] / 60, 1)
        else:
            typical_time = round(duration_normal['value'] / 60, 1)
        
        # Calculate range: Google typically shows ranges where max is ~1.8x min
        # Based on your screenshot showing 10-18 min, we'll use realistic ranges
        min_time = max(1, round(typical_time * 0.7))  # 30% less than typical
        max_time = round(typical_time * 1.3)  # 30% more than typical
        
        return {
            'min': min_time,
            'max': max_time,
            'typical': typical_time,
            'display': f"{min_time}-{max_time}",
            'conservative': max_time  # Use max for planning purposes
        }
    
    def _fallback_calculation(self, origin: str, destination: str) -> Dict[str, Optional[float]]:
        """
        Fallback calculation when Google Maps API is not available.
        This is a simple estimation and should be replaced with actual API calls.
        """
        logger.info("Using fallback travel time calculation")
        
        # Simple estimation: assume average speed and calculate based on distance
        # This is very rough and should be replaced with actual API integration
        try:
            # Use a simple geocoding service to estimate distance
            base_time = self._estimate_base_travel_time(origin, destination)
            
            # Apply traffic multipliers for different times
            travel_times = {
                'travel_time_830am': base_time * 1.3 if base_time else None,  # Rush hour
                'travel_time_930am': base_time * 1.1 if base_time else None,  # Light traffic
                'travel_time_midday': base_time * 1.0 if base_time else None,  # Normal traffic
                'travel_time_630pm': base_time * 1.4 if base_time else None,  # Heavy rush hour
                'travel_time_730pm': base_time * 1.2 if base_time else None   # Evening traffic
            }
            # Add *_display fields for frontend contract
            for slot in ['830am', '930am', 'midday', '630pm', '730pm']:
                key = f'travel_time_{slot}'
                val = travel_times[key]
                if val is not None:
                    min_time = max(1, round(val * 0.7))
                    max_time = round(val * 1.3)
                    travel_times[f'{key}_display'] = f"{min_time}-{max_time}"
                else:
                    travel_times[f'{key}_display'] = "N/A"
            return travel_times
        except Exception as e:
            logger.error(f"Fallback calculation failed: {e}")
            return {
                'travel_time_830am': None,
                'travel_time_930am': None,
                'travel_time_midday': None,
                'travel_time_630pm': None,
                'travel_time_730pm': None
            }
    
    def _estimate_base_travel_time(self, origin: str, destination: str) -> Optional[float]:
        """
        Estimate base travel time using a simple distance calculation.
        This is a fallback method and not very accurate.
        """
        try:
            # Use OpenStreetMap Nominatim for basic geocoding (free)
            origin_coords = self._geocode_address(origin)
            dest_coords = self._geocode_address(destination)
            
            if not origin_coords or not dest_coords:
                return None
            
            # Calculate straight-line distance
            distance_km = self._haversine_distance(
                origin_coords[0], origin_coords[1],
                dest_coords[0], dest_coords[1]
            )
            
            # Estimate driving time (assume 40 km/h average in city)
            estimated_time = (distance_km / 40) * 60  # Convert to minutes
            return round(estimated_time, 1)
            
        except Exception as e:
            logger.error(f"Base travel time estimation failed: {e}")
            return None
    
    def _geocode_address(self, address: str) -> Optional[tuple]:
        """Geocode address using Nominatim (OpenStreetMap)."""
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': address,
                'format': 'json',
                'limit': 1
            }
            headers = {'User-Agent': 'RentalRecon/1.0'}
            
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if data:
                return (float(data[0]['lat']), float(data[0]['lon']))
            return None
            
        except Exception as e:
            logger.error(f"Geocoding failed for {address}: {e}")
            return None
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points on Earth."""
        import math
        
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r
