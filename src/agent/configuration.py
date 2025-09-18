import os
from dataclasses import dataclass, field, fields
from typing import Annotated, Optional

from langchain_core.runnables import RunnableConfig
from langgraph.config import get_config
from loguru import logger

from agent.prompt import SYSTEM_PROMPT


@dataclass
class NoveraConfig:
    """The configuration of the agent"""

    system_prompt: str = field(
        default=SYSTEM_PROMPT,
        metadata={
            "description": "system prompt used by the agent that sets the context and behaviour"
        },
    )
    user_id: str = field(default="default")

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="GPT-4o mini",
        metadata={
            "description": "This is the name of the language model the agent uses for interaction"
        },
    )

    max_search_results: int = field(
        default=10,
        metadata={
            "description": "The maximum number of search results to return for each search query."
        },
    )

    @classmethod
    def from_context(cls):
        try:
            config = get_config()
        except RuntimeError:
            config = []

        configurable = config.get("configurable") or {}

        logger.info(f"configurable: {configurable}")

        _fields = {f.name for f in fields(cls) if f.init}

        logger.info(f"_fields  {_fields}")

        logger.info
        return cls(**{k: v for k, v in configurable.items() if k in _fields})

    @classmethod
    def from_runnables(cls, config: Optional[RunnableConfig] = None):

        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        logger.info(f"configurable : {configurable}")
        values = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }

        return cls(**{k: v for k, v in values.items() if v})
