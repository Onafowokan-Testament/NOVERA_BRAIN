"""Direction Agent - Tool Definitions.

Tool definitions for the direction agent including route retrieval,
location management, and memory saving using AWADOC pattern.
"""

from datetime import datetime
from typing import Any, Callable, Dict, List
from uuid import uuid4

from langchain.tools import ToolRuntime, tool
from loguru import logger

from agent.core.context import Context
from agent.core.state import MemoryNamespace
from .schema import CampusLocation
from .services import RouteService

route_service = RouteService()


# ============================================================================
# DIRECTION TOOLS
# ============================================================================


@tool
async def get_directions(
    start: CampusLocation,
    end: CampusLocation,
    runtime: ToolRuntime[Context],
) -> str:
    """Get walking directions between two campus locations.

    Args:
        start: Starting campus location
        end: Destination campus location
        runtime: Tool runtime with context and store access

    Returns:
        Walking directions as formatted string
    """
    logger.info(f"[Directions] Getting route from {start} to {end}")
    
    try:
        directions = await route_service.get_directions(start, end)
        result = " ".join(directions["instructions"])
        logger.debug(f"[Directions] Successfully retrieved directions")
        return result
    except ValueError as e:
        logger.warning(f"[Directions] Location not found: {e}")
        return "Location not found. Please check available locations with /get_locations"
    except Exception as e:
        logger.error(f"[Directions] Error getting directions: {e}")
        return "Please refer to campus map or ask staff for directions."


@tool
async def list_locations(runtime: ToolRuntime[Context]) -> str:
    """Get a list of all available campus locations.

    Returns:
        Formatted list of campus locations
    """
    logger.info("[Directions] Listing all campus locations")
    
    try:
        locations = route_service.list_available_locations()
        formatted = "\n".join(f"- {loc}" for loc in locations)
        return f"Available campus locations:\n{formatted}"
    except Exception as e:
        logger.error(f"[Directions] Error listing locations: {e}")
        return "Could not retrieve location list"


@tool
async def get_location_info(
    location: str,
    runtime: ToolRuntime[Context],
) -> str:
    """Get detailed information about a campus location.

    Args:
        location: Name of the campus location
        runtime: Tool runtime with context and store access

    Returns:
        Location information including coordinates
    """
    logger.info(f"[Directions] Getting info for location: {location}")
    
    try:
        info = route_service.get_location_info(location)
        if not info:
            return f"Location '{location}' not found"
        
        return (
            f"📍 {info['name']}\n"
            f"Longitude: {info['longitude']}\n"
            f"Latitude: {info['latitude']}"
        )
    except Exception as e:
        logger.error(f"[Directions] Error getting location info: {e}")
        return "Could not retrieve location information"


# ============================================================================
# MEMORY TOOL FACTORY
# ============================================================================


def create_direction_memory_tool(namespace: str, agent_name: str):
    """Create a memory tool for the direction agent.

    Args:
        namespace: Memory namespace (e.g., "direction_history")
        agent_name: Display name for the agent (e.g., "Direction")

    Returns:
        save_memory tool for this namespace
    """

    @tool(f"save_{namespace}_memory")
    async def save_direction_memory(
        content: str,
        context: str,
        runtime: ToolRuntime[Context],
    ) -> str:
        """Store direction-related information in user's profile.

        Args:
            content: The direction/location info to store (e.g., "User queried route to CST building")
            context: Additional context (e.g., "Queried during campus navigation session")
            runtime: Tool runtime with context and store access

        Returns:
            Confirmation message
        """
        try:
            logger.info(f"[{agent_name}] SAVING MEMORY: {content}")

            mem_id = uuid4()
            user_id = runtime.context.user_id
            store = runtime.store

            memory_data = {
                "content": content,
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "memory_id": str(mem_id),
                "agent": agent_name,
            }

            await store.aput(
                (user_id, namespace),
                key=str(mem_id),
                value=memory_data,
            )

            logger.info(
                f"[{agent_name}] Saved memory {mem_id} for user {user_id}"
            )
            return f"✓ Saved {agent_name} memory: {content}"

        except Exception as e:
            logger.error(f"[{agent_name}] Error saving memory: {e}")
            return f"Failed to save memory: {str(e)}"

    return save_direction_memory


# Create direction memory tool
save_direction_memory = create_direction_memory_tool(
    MemoryNamespace.DIRECTION, "Direction"
)

# ============================================================================
# TOOL LIST
# ============================================================================

TOOLS: List[Callable[..., Any]] = [
    get_directions,
    list_locations,
    get_location_info,
    save_direction_memory,
]

__all__ = [
    "TOOLS",
    "get_directions",
    "list_locations",
    "get_location_info",
    "save_direction_memory",
]

