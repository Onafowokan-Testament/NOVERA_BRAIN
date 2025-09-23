from typing import Literal, List, Optional
from pydantic import BaseModel, Field


CampusLocation = Literal[
    "medical_house",
    "cst",
    "clds",
    "engineering",
    "cmss",
    "dorcas_hall",
    "lydia_hall",
    "mary_hall",
    "deborah_hall",
    "library_center",
    "daniel_hall",
    "joseph_hall",
    "paul_hall",
    "peter_hall",
    "john_hall",
    "esther_hall",
    "sport_complex",
    "admirable_park",
    "chapel",
    "car_park",
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
