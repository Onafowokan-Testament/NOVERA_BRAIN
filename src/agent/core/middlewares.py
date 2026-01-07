"""Middleware hooks for agent memory and context management.

AWADOC pattern middleware for memory loading, context enrichment, and
response post-processing across all agents.
"""

from langchain.agents.middleware import before_agent
from langgraph.runtime import Runtime
from loguru import logger

from agent.core.context import Context
from agent.core.state import MemoryNamespace, State


def get_memory_middleware(namespace: MemoryNamespace, agent_name: str):
    """Create a memory loading middleware for a specific agent namespace.

    Args:
        namespace: Memory namespace (e.g., MemoryNamespace.DIRECTION)
        agent_name: Display name for the agent (e.g., "Direction")

    Returns:
        Middleware function that loads memories before agent processing
    """

    @before_agent
    async def load_user_memory(state: State, runtime: Runtime[Context]) -> dict:
        """Retrieve memories and enrich context without invoking the model.

        Args:
            state: Current agent state
            runtime: Runtime context with user info and store

        Returns:
            Dict with memory context to inject into state
        """
        logger.info(f"[{agent_name}] Loading memory context")

        try:
            user_id = runtime.context.user_id
            store = runtime.store
            messages = state.get("messages", [])

            # Build query from recent messages
            query = ""
            if messages:
                # Get last 3 messages for context
                recent_messages = messages[-3:] if len(messages) >= 3 else messages
                query = str(
                    [
                        (
                            m.get("content", "")
                            if isinstance(m, dict)
                            else getattr(m, "content", "")
                        )
                        for m in recent_messages
                    ]
                )

            # Retrieve recent memories from this namespace
            memories = await store.asearch(
                (user_id, namespace.value),
                query=query,
                limit=10,
            )

            if not memories:
                logger.info(f"[{agent_name}] No previous memories found")
                return {}

            # Format memories for inclusion in prompt
            formatted_memories = "\n".join(
                f"• {mem.value['content']}\n  Context: {mem.value['context']}\n  Date: {mem.value['timestamp']}"
                for mem in memories
            )

            memory_context = f"""
<{namespace.value}_history>
## Previous {agent_name} Interactions:

{formatted_memories}
</{namespace.value}_history>"""

            logger.info(f"[{agent_name}] Loaded {len(memories)} memories")

            # Inject memories into the message stream
            return {"messages": [{"role": "system", "content": memory_context}]}

        except Exception as e:
            logger.error(f"[{agent_name}] Error loading memories: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return {}

    return load_user_memory


__all__ = [
    "get_memory_middleware",
]
