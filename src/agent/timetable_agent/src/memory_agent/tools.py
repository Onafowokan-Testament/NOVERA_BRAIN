"""Tools module for the memory agent.
This module defines the core tools used by the agent to interact with memory storage
and timetable data.
"""

import uuid
from typing import Annotated, Any, Callable, Dict, List, Optional

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
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
    """Query and reason over the CST (College of Science and Technology) timetable using natural language

    This function creates an AI agent that can interpret and answer questions
    about the timetable data using natural language processing.

    The timetable system works as follows
    - Days are organized from Monday to Friday
    - Time slots run from 8am to 8pm
    - Course codes are formatted as three letters followed by numbers (e.g., MKT314, CHE417)
    - Multiple courses may share the same time slot in different rooms
    - Buildings include: CEDS, CHAPEL, CHE, CLDS/CMSS
    - Rooms are specified as LAB, LH (Lecture Hall), or specific room numbers



    Args:
        query (str): Natural language question about the timetable. Examples:
            - "What time is CHE417 on Monday?" (finds specific course timing)
            - "Show me all classes in MKT LAB" (finds classes in a specific room)
            - "What classes are in 400LH between 8am-11am?" (finds classes by room and time range)
            - "Where is MCM131 taught?" (finds room and building for a course)
        - Course codes must be written without spaces and in uppercase (e.g., MKT314, not MKT 314)



    """
    llm = ChatOpenAI(temperature=0)
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
    print(answer.get("output"))
    return answer.get("output")


async def process_tool_call(
    tool_call: dict, config: RunnableConfig, *, store: BaseStore
) -> str:
    """Process and execute a tool call while maintaining a memory record.

    This function handles the execution of tool calls and stores the interaction
    in the memory system for future reference.

    Args:
        tool_call (dict): Dictionary containing the tool call details including
            name and arguments.
        config (RunnableConfig): Configuration settings for the tool execution.
        store (BaseStore): Storage backend for maintaining memory records.

    Returns:
        str: Status message indicating the result of the tool call processing.

    Raises:
        Exception: If tool execution fails, with detailed error information.
    """
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

    status_msg = await upsert_memory(
        content={"args": tool_call["args"], "return_value": result},
        context=f"Tool execution: {tool_call['name']}",
        config=config,
        store=store,
    )
    return status_msg


# Available tools and their mappings
TOOLS: List[Callable[..., Any]] = [talk_with_timetable]
TOOLS_MAP: Dict[str, Callable[..., Any]] = {
    (t.name if hasattr(t, "name") else t.__name__): (
        t.coroutine if hasattr(t, "coroutine") else t
    )
    for t in TOOLS
}
