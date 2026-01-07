"""Agent-specific configuration.

Separate configuration for agent orchestration and sub-agents.
"""

from dataclasses import dataclass, field, fields
from typing import Annotated, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.config import get_config

from settings.logger_config import logger


@dataclass
class AgentConfig:
    """Configuration for the NOVERA agent orchestrator."""

    system_prompt: str = field(
        default="You are NOVERA, a helpful university assistant.",
        metadata={
            "description": "System prompt that defines the agent's behavior and context"
        },
    )

    user_id: str = field(
        default="default",
        metadata={"description": "Unique identifier for the current user"},
    )

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/gpt-4o-mini",
        metadata={"description": "LLM model identifier"},
    )

    max_search_results: int = field(
        default=10,
        metadata={"description": "Maximum number of search results per query"},
    )

    temperature: float = field(
        default=0.7,
        metadata={"description": "LLM temperature for generation"},
    )

    @classmethod
    def from_context(cls) -> "AgentConfig":
        """Load configuration from LangGraph context.

        Returns:
            AgentConfig: Configuration loaded from context or defaults.
        """
        try:
            config = get_config()
        except RuntimeError:
            config = {}

        configurable = config.get("configurable") or {}

        logger.debug(f"Loading agent config from context: {configurable}")

        _fields = {f.name for f in fields(cls) if f.init}

        return cls(**{k: v for k, v in configurable.items() if k in _fields})

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "AgentConfig":
        """Load configuration from RunnableConfig.

        Args:
            config: RunnableConfig object or None.

        Returns:
            AgentConfig: Configuration loaded from config or defaults.
        """
        import os

        configurable = (
            config.get("configurable") if config and "configurable" in config else {}
        )

        logger.debug(f"Loading agent config from runnable: {configurable}")

        values = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }

        return cls(**{k: v for k, v in values.items() if v})
