"""Supervisor Agent - Multi-agent orchestration using AWADOC pattern.

The supervisor agent coordinates between different specialized agents:
- Direction Agent: Campus navigation and directions
- QA Agent: Document retrieval and question answering
- Timetable Agent: Class schedules and timetable queries

Uses LangChain's create_agent with middleware for memory management.
"""

from datetime import datetime
from typing import Callable, List

from decouple import config
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from agent.core.agent_handler import create_agent_handler
from agent.core.context import Context
from agent.core.middlewares import get_memory_middleware
from agent.core.state import MemoryNamespace
from agent.direction_agent import initiate_direction_agent
from agent.qa_agent import initiate_qa_agent
from agent.timetable_agent import initiate_timetable_agent

from .supervisor_prompts import SUPERVISOR_SYSTEM_PROMPT

# Initialize the language model
llm = init_chat_model(model_provider="openai", model="gpt-4o-mini")
AGENT_NAME: str = config("SUPERVISOR_AGENT_NAME", default="supervisor_agent")

# Create memory middleware for supervisor-specific namespace
get_supervisor_middleware = get_memory_middleware(
    MemoryNamespace.SUPERVISOR, "Supervisor"
)


def _create_supervisor_tools() -> List[Callable]:
    """Create tool-wrapped handlers for all sub-agents.

    Returns:
        List of callable agent handlers as tools
    """
    try:
        # Initialize all sub-agents
        direction_agent = initiate_direction_agent()
        qa_agent = initiate_qa_agent()
        timetable_agent = initiate_timetable_agent()

        # Wrap each agent as a tool
        direction_handler = create_agent_handler(direction_agent, "Direction Agent")
        qa_handler = create_agent_handler(qa_agent, "QA Agent")
        timetable_handler = create_agent_handler(timetable_agent, "Timetable Agent")

        return [direction_handler, qa_handler, timetable_handler]

    except Exception as e:
        print(f"Error creating supervisor tools: {e}")
        raise


# Lazy initialization of tools to avoid circular imports
_tools = None


def _get_supervisor_tools() -> List[Callable]:
    """Get or initialize supervisor tools (lazy loading)."""
    global _tools
    if _tools is None:
        _tools = _create_supervisor_tools()
    return _tools


def initiate_supervisor_agent():
    """Create and return the supervisor agent using LangChain's create_agent.

    The supervisor agent:
    - Routes queries to appropriate specialized agents
    - Manages conversation flow and memory
    - Provides unified interface to the user

    Returns:
        Compiled supervisor agent graph with multi-agent coordination
    """
    # Get supervisor tools (sub-agent handlers)
    tools = _get_supervisor_tools()

    # Format system prompt with current time
    system_prompt = SUPERVISOR_SYSTEM_PROMPT.format(time=datetime.now().isoformat())

    # Use LangChain's create_agent for simplified graph construction
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        context_schema=Context,
        middleware=[get_supervisor_middleware],
    )

    return agent


__all__ = ["initiate_supervisor_agent", "llm", "AGENT_NAME"]
