"""Runtime context schema for agents."""

import os
from dataclasses import dataclass, field, fields
from typing import Annotated, Any, Optional

from langchain_core.runnables import RunnableConfig


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
        metadata={
            "description": "The LLM model to use. Format: provider/model-name"
        },
    )

    thread_id: Optional[str] = field(
        default=None,
        metadata={"description": "Thread ID for conversation tracking"},
    )

    @classmethod
    def from_config(cls, config: Optional[RunnableConfig] = None) -> "Context":
        """Create Context from RunnableConfig.
        
        Args:
            config: LangGraph RunnableConfig
            
        Returns:
            Context instance with configurable values
        """
        if not config:
            return cls()

        configurable = config.get("configurable", {})
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }

        return cls(**{k: v for k, v in values.items() if v})


__all__ = ["Context"]
