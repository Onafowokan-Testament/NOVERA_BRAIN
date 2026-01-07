"""Agent configuration - now consolidated in settings.agent_config.

This file is kept for backward compatibility but imports from settings.
All agent configuration is now in src/settings/agent_config.py
"""

# Import for backward compatibility
from settings.agent_config import AgentConfig as NoveraConfig  # noqa: F401

__all__ = ["NoveraConfig"]

