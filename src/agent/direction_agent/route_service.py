from typing import Dict, List, Optional

import aiohttp
from settings.logger_config import logger

from settings.config import Settings

CAMPUS_LOCATIONS = {
    # Academic Buildings - Format: [longitude, latitude] for ORS API
    "cst": [3.1585897510423453, 6.673565731966269],
    "coe": [3.162361149395122, 6.674816398942319],
    "clds": [3.1599233869580625, 6.6717913811989575],
    # Hostels
    "peter_hall": [3.1541367839739616, 6.668924845575664],
    "paul_hall": [3.15397897124805, 6.6706503368936065],
    "john_hall": [3.1531559598384122, 6.66946253608972],
    "daniel_hostel": [3.152206907323679, 6.6718776344860515],
    "esther_hostel": [3.1550478619102664, 6.669696653292088],
    "joseph_hostel": [3.152647317314176, 6.670744018354111],
    "mary_hostel": [3.154787337675236, 6.6720563020157195],
    # Facilities
    "chapel": [3.1580314848575264, 6.669906126466808],
    "library": [3.156682826741583, 6.670414135958599],
    "caf1": [3.154075358894256, 6.669644512814657],
    "caf2": [3.16219865283879, 6.672434726237397],
    "sports_complex": [3.16121085053408, 6.673824124851311],
    "health_center": [3.155532845096147, 6.668285053769483],
    # Landmarks
    "main_gate": [3.1642268933317697, 6.678086250674037],
    "covenant_plaza": [3.1585675154909048, 6.670271554723794],
    "freedom_square": [3.160238439915539, 6.670787976113542],
}


class RouteService:
    def __init__(self):
        self.api_key = Settings.ORS_API_KEY
        self.base_url = "https://api.openrouteservice.org/geocode"
        self.directions_url = "https://api.openrouteservice.org/v2/directions"
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

    def _normalize_location_name(self, place_name: str) -> str:
        """Normalize and resolve aliases for location names"""
        normalized = place_name.lower().strip().replace(" ", "_")
        logger.info(f"Normalized place name: {normalized}")
        return normalized

    def get_coordinates(self, place_name: str) -> Optional[List[float]]:
        """Get coordinates from local mapping first"""
        normalized = self._normalize_location_name(place_name)
        coords = CAMPUS_LOCATIONS.get(normalized)

        if coords:
            logger.info(f"Found local coordinates for {place_name}: {coords}")
            return coords

        logger.warning(f"No local coordinates found for {place_name}")
        return None

    async def get_directions(self, start_place: str, end_place: str) -> Dict:
        """Get walking directions between two places

        Args:
            start_place: Name of starting location
            end_place: Name of destination

        Returns:
            Dict containing route information
        """
        # Get coordinates from local mapping
        try:
            # Validate API key
            if not self.api_key:
                raise ValueError("OpenRouteService API key not configured")

            start_coords = self.get_coordinates(start_place)
            if not start_coords:
                raise ValueError(
                    f"Unknown location: {start_place}. Use /get_locations to see available places."
                )

            end_coords = self.get_coordinates(end_place)
            if not end_coords:
                raise ValueError(
                    f"Unknown location: {end_place}. Use list_locations() to see available places."
                )

            # Check if same location
            if start_coords == end_coords:
                return {
                    "from": start_place,
                    "to": end_place,
                    "distance": 0,
                    "duration": 0,
                    "instructions": ["You are already at the destination."],
                    "same_location": True,
                }

            # Call OpenRouteService API
            # IMPORTANT: ORS expects coordinates in [longitude, latitude] format
            # Our CAMPUS_LOCATIONS are stored in this format
            payload = {
                "coordinates": [start_coords, end_coords],
                "instructions": True,
                "preference": "shortest",
                "units": "m",
                "language": "en",
                "geometry": True,
            }

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        f"{self.directions_url}/foot-walking",
                        headers=self.headers,
                        json=payload,
                    ) as response:
                        if response.status == 429:  # Rate limit
                            raise ValueError(
                                "API rate limit exceeded. Please try again later."
                            )
                        elif response.status != 200:
                            error_text = await response.text()
                            logger.error(f"API Error: {error_text}")
                            raise ValueError(
                                f"Direction service error: {response.status}"
                            )

                        route_data = await response.json()
                        logger.info("Retrieved route data successfully")

                        return self._format_response(route_data, start_place, end_place)

                except aiohttp.ClientError as e:
                    logger.error(f"Network error: {str(e)}")
                    raise ValueError("Could not connect to direction service")

        except ValueError:
            # Re-raise ValueError as is
            raise
        except Exception as e:
            logger.error(f"Failed to get directions: {str(e)}")
            raise ValueError(f"Failed to get directions: {str(e)}")

    def _format_response(self, route_data: Dict, start: str, end: str) -> Dict:
        """Format OpenRouteService response"""
        if not route_data or "routes" not in route_data:
            raise Exception("No routes found in response")

        route = route_data["routes"][0]
        segments = route.get("segments", [{}])[0]

        return {
            "from": start,
            "to": end,
            "distance": segments.get("distance", 0),  # meters
            "duration": segments.get("duration", 0),  # seconds
            "instructions": self._extract_instructions(segments),
            "geometry": route.get("geometry"),
        }

    def _extract_instructions(self, segment: Dict) -> List[str]:
        """Extract turn-by-turn instructions"""
        instructions = []

        for step in segment.get("steps", []):
            instruction = step.get("instruction", "")
            distance = step.get("distance", 0)

            if instruction and distance > 0:
                instructions.append(f"{instruction} ({round(distance)}m)")
            elif instruction:
                instructions.append(instruction)

        return instructions if instructions else ["Walk to destination"]

    def list_available_locations(self) -> List[str]:
        """Get list of all available campus locations"""
        return sorted(CAMPUS_LOCATIONS.keys())

    def add_location(self, name: str, longitude: float, latitude: float):
        """Add a new location dynamically"""
        normalized = name.lower().strip().replace(" ", "_")
        CAMPUS_LOCATIONS[normalized] = [longitude, latitude]
        logger.info(f"Added location: {normalized} at [{longitude}, {latitude}]")

    def get_location_info(self, place_name: str) -> Optional[Dict]:
        """Get detailed info about a location"""
        coords = self.get_coordinates(place_name)
        if coords:
            return {
                "name": place_name,
                "coordinates": coords,
                "longitude": coords[0],
                "latitude": coords[1],
            }
        return None


# Initialize service
route_service = RouteService()
