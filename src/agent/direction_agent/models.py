from typing import List, Literal, Optional

from pydantic import BaseModel

CampusLocation = Literal[
    # Academic Buildings
    "cst", "coe", "clds",
    # Hostels
    "peter_hall", "paul_hall", "john_hall",
    "daniel_hostel", "esther_hostel", "joseph_hostel", "mary_hostel",
    # Facilities
    "chapel", "library", "caf1", "caf2",
    "sports_complex", "health_center",
    # Landmarks
    "main_gate", "covenant_plaza", "freedom_square",
]  


# ---------- Pydantic Models ----------


class DirectionRequest(BaseModel):
    start: CampusLocation
    end: CampusLocation


class DirectionResponse(BaseModel):
    from_location: str
    to_location: str
    steps: List[str]
    time: str
    landmarks: List[str]
    difficulty: Optional[str] = "unknown"
