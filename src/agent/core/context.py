"""Runtime context schema for agents."""

from dataclasses import dataclass, field
from typing import Annotated


@dataclass(kw_only=True)
class Context:
    """Runtime context passed to all agents.

    Contains user-specific information and configuration
    accessed via runtime.context.user_id, etc.
    """

    user_id: str = field(
        default="default_user",
        metadata={"description": "Unique identifier for the user"},
    )

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="gpt-4o-mini",
        metadata={"description": "The LLM model to use. Format: provider/model-name"},
    )
