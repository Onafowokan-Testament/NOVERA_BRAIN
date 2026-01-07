"""QA Agent - Document retrieval and question answering.

AWADOC pattern implementation with create_agent for document search,
memory management, and conversational retrieval.
"""

from datetime import datetime

from decouple import config
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from agent.core.context import Context
from agent.core.middlewares import get_memory_middleware
from agent.core.state import MemoryNamespace
from .prompts import RESPONSE_SYSTEM_PROMPT
from .tools import TOOLS

# Initialize the language model
llm = init_chat_model(model_provider="openai", model="gpt-4o-mini")
AGENT_NAME: str = config("QA_AGENT_NAME", default="qa_agent")

# Create memory middleware for QA-specific namespace
get_qa_middleware = get_memory_middleware(
    MemoryNamespace.QA, "QA"
)


def initiate_qa_agent():
    """Create and return a QA agent using LangChain's create_agent.
    
    Returns:
        Compiled agent graph with document retrieval, tool calling, and memory management.
    """
    # Format system prompt with current time
    system_prompt = RESPONSE_SYSTEM_PROMPT.format(
        retrieved_docs="",
        system_time=datetime.now().isoformat()
    )
    
    # Use LangChain's create_agent for simplified graph construction
    agent = create_agent(
        model=llm,
        tools=TOOLS,
        system_prompt=system_prompt,
        context_schema=Context,
        middleware=[get_qa_middleware],
    )
    
    return agent


__all__ = ["initiate_qa_agent", "llm", "AGENT_NAME"]

