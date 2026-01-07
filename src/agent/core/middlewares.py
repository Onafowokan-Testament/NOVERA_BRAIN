"""Middleware hooks for agent memory and context management."""

from typing import Any, Callable, Dict, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.store.base import BaseStore
from settings.logger_config import logger

from agent.core.state import MemoryNamespace, State
from agent.core.context import Context


async def create_memory_loader_middleware(
    namespace: MemoryNamespace, agent_name: str
) -> Callable:
    """Create middleware to load memories before agent processing.
    
    Args:
        namespace: Memory namespace for this agent
        agent_name: Display name of agent
        
    Returns:
        Async middleware function
    """

    async def load_memories(state: State, config: Dict[str, Any], store: BaseStore) -> Dict[str, Any]:
        """Load relevant memories from PostgreSQL.
        
        Args:
            state: Current agent state
            config: LangGraph config with user info
            store: PostgreSQL store for semantic search
            
        Returns:
            Dict with memory context to inject
        """
        try:
            configurable = config.get("configurable", {})
            user_id = configurable.get("user_id", "default_user")
            
            logger.info(f"[{agent_name}] Loading memories for user {user_id}")

            # Search for relevant memories using semantic search
            memories = await store.asearch(
                key=(user_id, namespace.value),
                query=str([m.content for m in state.messages[-3:]]),  # Last 3 messages as query
                limit=10,
            )

            if not memories:
                logger.debug(f"[{agent_name}] No memories found")
                return {"memory_context": ""}

            # Format memories for injection
            formatted = "\n".join(
                f"[Memory {i}]: {mem.value.get('content', '')} (similarity: {mem.score:.2f})"
                for i, mem in enumerate(memories, 1)
            )

            logger.info(f"[{agent_name}] Loaded {len(memories)} memories")
            return {"memory_context": formatted}

        except Exception as e:
            logger.error(f"[{agent_name}] Error loading memories: {e}")
            return {"memory_context": ""}

    return load_memories


def create_memory_save_tool(namespace: MemoryNamespace, agent_name: str) -> Callable:
    """Factory to create memory-saving tools for any namespace.
    
    Args:
        namespace: Memory namespace for this agent
        agent_name: Display name of agent
        
    Returns:
        Async tool function
    """

    async def save_memory(
        content: str,
        context: str,
        user_id: str,
        store: BaseStore,
    ) -> str:
        """Save information to user's persistent memory.

        Args:
            content: What to save (e.g., "User asked about campus directions")
            context: When/why/details (e.g., "Location query at 2025-01-07")
            user_id: User ID for memory scoping
            store: PostgreSQL store

        Returns:
            Confirmation message
        """
        try:
            from datetime import datetime
            from uuid import uuid4

            mem_id = str(uuid4())
            memory_data = {
                "content": content,
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "memory_id": mem_id,
                "agent": agent_name,
            }

            await store.aput(
                key=(user_id, namespace.value),
                key_suffix=mem_id,  # Unique ID within namespace
                value=memory_data,
            )

            logger.info(f"[{agent_name}] Saved memory: {content[:50]}...")
            return f"✓ Saved {agent_name} memory"

        except Exception as e:
            logger.error(f"[{agent_name}] Error saving memory: {e}")
            return f"Failed to save memory: {str(e)}"

    return save_memory


__all__ = [
    "create_memory_loader_middleware",
    "create_memory_save_tool",
]
