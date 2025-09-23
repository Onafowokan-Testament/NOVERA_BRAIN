"""Define he agent's tools."""

import json
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any, Callable, Dict, List, Optional

import aiofiles
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from langgraph.store.base import BaseStore
from loguru import logger

from .configuration import Configuration
from .models import CampusLocation


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
        content: The main content of the memory. For example:
            "User expressed interest in learning about French."
        context: Additional context for the memory. For example:
            "This was mentioned while discussing career options in Europe."
        memory_id: ONLY PROVIDE IF UPDATING AN EXISTING MEMORY.
        The memory to overwrite.
    """

    mem_id = memory_id or uuid.uuid4()
    user_id = Configuration.from_runnable_config(config).user_id
    await store.aput(
        ("memories", user_id, "directions"),
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
    A campus navigator tool

    Args:

    start: Start location
    end: end locatio

    """
    async with aiofiles.open(
        "src/agent/direction_agent/data/campus_direction.json", "r"
    ) as f:
        content = await f.read()
        content = json.loads(content)

    try:
        road_map = start + "_to_" + end
        directions = content.get("directions", "")
        map = directions.get(road_map, "")

        return map
    except Exception:
        logger.error("Encountered an error while getting direction")


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

    status_msg = await upsert_memory(
        content={"args": tool_call["args"], "return_value": result},
        context="Calling " + tool_call["name"],
        memory_id=datetime.now(tz=UTC),
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
