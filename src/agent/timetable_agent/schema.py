"""Timetable Agent - Configuration and State.

Schema definitions for the timetable agent including configuration
and state management for class schedule queries.
"""

import os
from dataclasses import dataclass, field, fields
from typing import Any, Optional

from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import add_messages
from typing_extensions import Annotated

from . import prompts

# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass(kw_only=True)
class Configuration:
    """Timetable agent configuration."""

    user_id: str = "default"
    """The ID of the user to track timetable queries."""

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/gpt-4o-mini",
        metadata={"description": "The language model to use (provider/model-name)."},
    )

    system_prompt: str = prompts.SYSTEM_PROMPT
    """System prompt for the timetable agent."""

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create Configuration from RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v})


# ============================================================================
# STATE
# ============================================================================


@dataclass(kw_only=True)
class State:
    """Timetable agent graph state."""

    messages: Annotated[list[AnyMessage], add_messages]
    """Conversation messages with deduplication."""


__all__ = [
    "Configuration",
    "State",
]
