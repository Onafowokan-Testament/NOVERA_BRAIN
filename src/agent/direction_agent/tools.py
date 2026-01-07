"""Direction Agent - Tool Definitions.

Tool definitions for the direction agent including memory management,
route retrieval, and location management.
"""

import uuid
from typing import Annotated, Any, Callable, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from langgraph.store.base import BaseStore

from settings.logger_config import logger

from .schema import Configuration, CampusLocation
from .services import RouteService

route_service = RouteService()


async def upsert_memory(
    content: str,
    context: str,
    *,
    memory_id: Optional[uuid.UUID] = None,
    # Hide these arguments from the model.
    config: Annotated[RunnableConfig, InjectedToolArg],
    store: Annotated[BaseStore, InjectedToolArg],
):
    """Upsert a memory in the database.

    If a memory conflicts with an existing one, then just UPDATE the
    existing one by passing in memory_id - don't create two memories
    that are the same. If the user corrects a memory, UPDATE it.

    Args:
        content: The summarised main content of the memory in strings. For example:
            "User expressed interest in learning about French."
        context: Additional context for the memory. For example:
            "This was mentioned while discussing career options in Europe."
        memory_id: ONLY PROVIDE IF UPDATING AN EXISTING MEMORY.
        The memory to overwrite.
    """

    mem_id = memory_id or uuid.uuid4()
    user_id = Configuration.from_runnable_config(config).user_id
    await store.aput(
        ("directions", user_id, "memories"),
        key=str(mem_id),
        value={"content": content, "context": context},
    )
    return f"Stored memory {mem_id}"


async def get_directions(
    start: CampusLocation,
    end: CampusLocation,
    config: Annotated[RunnableConfig, InjectedToolArg] = None,
    store: Annotated[BaseStore, InjectedToolArg] = None,
):
    """
    Get walking directions between two campus locations.

     Args:
         start: Starting location
         end: Destination location

     Returns:
         Dict containing walking directions

    """

    try:

        directions = await route_service.get_directions(start, end)
        return " ".join(directions["instructions"])
    except ValueError:
        # Handle known location errors
        return "Location not found. Please check available locations"
    except Exception as e:
        # Fallback to default directions if API fails
        logger.error(f"Error getting directions: {str(e)}")
        return "Please refer to campus map or ask staff for directions."


async def process_tool_call(tool_call, config: RunnableConfig, *, store: BaseStore):
    print(tool_call)

    function_name = tool_call["name"]
    args = tool_call["args"]
    function = TOOLS_MAP[function_name]

    try:
        result = await function(**args, config=config, store=store)
    except Exception as e:
        print(e)
        result = await function(**args)
    # print(result)

    logger.info(f"Upserting for {function_name} ...")

    await upsert_memory(
        content={"args": tool_call["args"], "return_value": result},
        context="Calling " + tool_call["name"],
        memory_id=None,  # or uuid.uuid4() if you want unique IDs
        config=config,
        store=store,
    )
    return result


TOOLS: List[Callable[..., Any]] = [get_directions]
TOOLS_MAP: Dict[str, Callable[..., Any]] = {
    (t.name if hasattr(t, "name") else t.__name__): (
        t.coroutine if hasattr(t, "coroutine") else t
    )
    for t in TOOLS
}
