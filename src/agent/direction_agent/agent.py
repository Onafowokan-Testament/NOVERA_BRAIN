"""Direction Agent - Campus Navigation with Memory Management.

AWADOC pattern implementation using create_agent with middleware,
context, and memory namespaces for direction-specific logic.
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
AGENT_NAME: str = config("DIRECTION_AGENT_NAME", default="direction_agent")

# Create memory middleware for direction-specific namespace
get_direction_middleware = get_memory_middleware(
    MemoryNamespace.DIRECTION, "Direction"
)


def initiate_direction_agent():
    """Create and return a direction agent using LangChain's create_agent.
    
    Returns:
        Compiled agent graph with tool calling, memory management, and automatic routing.
    """
    # Format system prompt with current time
    system_prompt = SYSTEM_PROMPT.format(time=datetime.now().isoformat())
    
    # Use LangChain's create_agent for simplified graph construction
    # Automatically handles:
    # - Tool binding and invocation
    # - Message routing via tool calls
    # - Memory context loading via middleware
    agent = create_agent(
        model=llm,
        tools=TOOLS,
        system_prompt=system_prompt,
        context_schema=Context,
        middleware=[get_direction_middleware],
    )
    
    return agent


__all__ = ["initiate_direction_agent", "llm", "AGENT_NAME"]

