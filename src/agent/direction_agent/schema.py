"""Direction Agent - Configuration, State, and Models.

Consolidated schema definitions for the direction agent including:
- Configuration: Runnable config with user_id, model, system_prompt
- State: Graph state with messages
- Models: Pydantic models for direction requests/responses
"""

import os
from dataclasses import dataclass, field, fields
from typing import Any, List, Literal, Optional

from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import add_messages
from pydantic import BaseModel
from typing_extensions import Annotated

from . import prompts

# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass(kw_only=True)
class Configuration:
    """Direction agent configuration."""

    user_id: str = "default"
    """The ID of the user to track direction history."""
    
    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/gpt-4o-mini",
        metadata={
            "description": "The language model to use (provider/model-name)."
        },
    )
    
    system_prompt: str = prompts.SYSTEM_PROMPT
    """System prompt for the direction agent."""

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
    """Direction agent graph state."""

    messages: Annotated[list[AnyMessage], add_messages]
    """Conversation messages with deduplication."""


# ============================================================================
# PYDANTIC MODELS
# ============================================================================


CampusLocation = Literal[
    # Academic Buildings
    "cst",
    "coe",
    "clds",
    # Hostels
    "peter_hall",
    "paul_hall",
    "john_hall",
    "daniel_hostel",
    "esther_hostel",
    "joseph_hostel",
    "mary_hostel",
    # Facilities
    "chapel",
    "library",
    "caf1",
    "caf2",
    "sports_complex",
    "health_center",
    # Landmarks
    "main_gate",
    "covenant_plaza",
    "freedom_square",
]


class DirectionRequest(BaseModel):
    """Request for campus directions."""

    start: CampusLocation
    end: CampusLocation


class DirectionResponse(BaseModel):
    """Response with campus directions."""

    from_location: str
    to_location: str
    steps: List[str]
    time: str
    landmarks: List[str]
    difficulty: Optional[str] = "unknown"


__all__ = [
    "Configuration",
    "State",
    "CampusLocation",
    "DirectionRequest",
    "DirectionResponse",
]
