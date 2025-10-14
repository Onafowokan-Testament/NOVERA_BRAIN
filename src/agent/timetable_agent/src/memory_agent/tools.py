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
    """Query the timetable data using natural language.

    This function creates an AI agent that can interpret and answer questions
    about the timetable data using natural language processing.

    Args:
        query (str): Natural language question about the timetable. Examples:
            - "What classes are scheduled for Monday?"
            - "When is the next mathematics class?"
            - "How many hours of physics are there this week?"
            -Note course code do not have spaces in between them, if user writes csc 224, he means CSC224 in caps

    Returns:
         Response containing the answer to the query and any relevant
            timetable information.

    """
    llm = ChatOpenAI(temperature=0.5)
    try:
        agent_executor = create_csv_agent(
            llm,
            "src/agent/timetable_agent/document/timetable_formatted.csv",
            verbose=True,
            agent_type="tool-calling",
            allow_dangerous_code=True,
        )

    except Exception as e:
        logger.error(f"Failed to create CSV agent: {str(e)}")
        return {"error": "We had an error processing your request."}
    answer = await agent_executor.ainvoke(query)
   
    return answer


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
