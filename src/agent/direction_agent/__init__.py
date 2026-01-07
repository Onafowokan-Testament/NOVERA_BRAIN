"""Direction Agent - Handles campus directions and location-based queries."""

from .graph import initiate_direction_agent

# Create the default graph instance
graph = initiate_direction_agent()

__all__ = ["graph", "initiate_direction_agent"]
