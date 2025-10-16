"""Tools module for the memory agent.
This module defines the core tools used by the agent to interact with memory storage
and timetable data.
"""

import uuid
from typing import Annotated, Any, Callable, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from langchain_experimental.agents.agent_toolkits import create_csv_agent
from langchain_openai import ChatOpenAI
from langgraph.store.base import BaseStore
from settings.logger_config import logger

from .configuration import Configuration


async def upsert_memory(
    content: str,
    context: str,
    *,
    memory_id: Optional[uuid.UUID] = None,
    config: Annotated[RunnableConfig, InjectedToolArg],
    store: Annotated[BaseStore, InjectedToolArg],
) -> str:
    """Create or update a memory entry in the database.

    This function handles both creation of new memories and updating existing ones.
    It ensures that duplicate memories are not created by allowing updates to
    existing memories through the memory_id parameter.

    Args:
        content (str): The primary content of the memory. Should be a clear, concise
            summary of the main information. Example: "User prefers morning classes
            for mathematics."
        context (str): Supporting information that provides additional background
            or circumstances. Example: "Mentioned during schedule planning for
            spring semester."
        memory_id (Optional[uuid.UUID]): Unique identifier for updating an existing
            memory. If None, a new memory will be created.
        config (RunnableConfig): Configuration settings injected by the system.
        store (BaseStore): The storage backend injected by the system.

    Returns:
        str: Confirmation message with the memory ID.

    Example:
        >>> await upsert_memory(
        ...     content="User prefers morning classes",
        ...     context="Schedule planning discussion",
        ...     config=config,
        ...     store=store
        ... )
        'Stored memory 123e4567-e89b-12d3-a456-426614174000'
    """
    mem_id = memory_id or uuid.uuid4()
    user_id = Configuration.from_runnable_config(config).user_id
    await store.aput(
        ("directions", user_id, "memories"),
        key=str(mem_id),
        value={"content": content, "context": context},
    )
    return f"Stored memory {mem_id}"



async def talk_with_timetable(
    query: str,
    config: Annotated[RunnableConfig, InjectedToolArg] = None,
    store: Annotated[BaseStore, InjectedToolArg] = None,
) -> dict:
    """Query and reason over the CST timetable using natural language

    Note, course codes do not have space, and they are in all caps e.g CSC416, CSC412 not csc412 or CSC 413
     



    """
    llm = ChatOpenAI(temperature=0.5)
    try:
        agent_executor = create_csv_agent(
            llm,
            "src/agent/timetable_agent/document/td2.csv",
            verbose=True,
            agent_type="tool-calling",
            allow_dangerous_code=True,
        )

    except Exception as e:
        logger.error(f"Failed to create CSV agent: {str(e)}")
        return {"error": "We had an error processing your request."}
    answer = await agent_executor.ainvoke(query)
    logger.info(f"Timetable query: {query}, Answer: {answer['output']}")
   
    return answer["output"]



async def process_tool_call(  
    tool_call: dict, config: RunnableConfig, *, store: BaseStore
) -> str:
    """Process and execute a tool call while maintaining a memory record."""
    print(tool_call)

    function_name = tool_call["name"]
    args = tool_call["args"]
    function = TOOLS_MAP[function_name]

    try:
        result = await function(**args, config=config, store=store)
    except Exception as e:
        logger.error(f"Tool call failed: {str(e)}")
        result = await function(**args)

    logger.info(f"Recording memory for tool call: {function_name}")

    await upsert_memory(
        content={"args": tool_call["args"], "return_value": result},
        context=f"Tool execution: {tool_call['name']}",
        config=config,
        store=store,
    )
    return result


# Available tools and their mappings
TOOLS: List[Callable[..., Any]] = [talk_with_timetable]
TOOLS_MAP: Dict[str, Callable[..., Any]] = {
    (t.name if hasattr(t, "name") else t.__name__): (
        t.coroutine if hasattr(t, "coroutine") else t
    )
    for t in TOOLS
}
