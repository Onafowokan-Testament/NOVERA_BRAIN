"""Direction Agent - Campus navigation and direction queries.

Handles user queries about getting directions on campus with memory persistence.
"""

from .agent import initiate_direction_agent
from .schema import Configuration, State, DirectionRequest, DirectionResponse
from .services import RouteService

# Create the default graph instance
graph = initiate_direction_agent()

__all__ = [
    "graph",
    "initiate_direction_agent",
    "Configuration",
    "State",
    "DirectionRequest",
    "DirectionResponse",
    "RouteService",
]
