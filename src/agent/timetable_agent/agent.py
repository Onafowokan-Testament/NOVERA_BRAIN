"""Timetable Agent - Class schedule and timetable queries.

AWADOC pattern implementation with create_agent for schedule queries,
memory management, and conversational retrieval.
"""

from datetime import datetime

from decouple import config
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from agent.core.context import Context
from agent.core.middlewares import get_memory_middleware
from agent.core.state import MemoryNamespace
from .prompts import SYSTEM_PROMPT
from .tools import TOOLS

# Initialize the language model
llm = init_chat_model(model_provider="openai", model="gpt-4o-mini")
AGENT_NAME: str = config("TIMETABLE_AGENT_NAME", default="timetable_agent")

# Create memory middleware for timetable-specific namespace
get_timetable_middleware = get_memory_middleware(
    MemoryNamespace.TIMETABLE, "Timetable"
)


def initiate_timetable_agent():
    """Create and return a timetable agent using LangChain's create_agent.
    
    Returns:
        Compiled agent graph with schedule queries, tool calling, and memory management.
    """
    # Format system prompt with current time
    system_prompt = SYSTEM_PROMPT.format(time=datetime.now().isoformat())
    
    # Use LangChain's create_agent for simplified graph construction
    agent = create_agent(
        model=llm,
        tools=TOOLS,
        system_prompt=system_prompt,
        context_schema=Context,
        middleware=[get_timetable_middleware],
    )
    
    return agent


__all__ = ["initiate_timetable_agent", "llm", "AGENT_NAME"]
