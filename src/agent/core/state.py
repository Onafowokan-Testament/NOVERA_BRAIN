"""Core state and memory namespace definitions for NOVERA agents."""

from enum import Enum
from typing import Annotated, List

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langgraph.prebuilt.chat_agent_executor import AgentState


class MemoryNamespace(str, Enum):
    """Memory namespaces for agent isolation.

    Each agent has an isolated memory namespace in PostgreSQL.
    Allows semantic search within each agent's context.
    """

    GENERAL = "general_profile"  # Supervisor stores user profile info
    DIRECTION = "direction_history"  # Direction agent stores navigation history
    QA = "qa_history"  # QA agent stores question/answer history
    TIMETABLE = "timetable_history"  # Timetable agent stores schedule queries
    SUPERVISOR = "supervisor_context"  # Supervisor-level context


class State(AgentState):
    """Main conversation state for agents.

    Inherits from LangGraph's AgentState which includes:
    - messages: Annotated list with add_messages reducer (deduplication)
    """

    messages: Annotated[List[AnyMessage], add_messages]
    """Conversation messages - automatically deduplicated by add_messages reducer."""


__all__ = ["State", "MemoryNamespace"]
