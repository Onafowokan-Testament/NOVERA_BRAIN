"""Agent handler factory for wrapping agents as tools for supervisor coordination.

This module provides utilities to wrap compiled agents as callable tools
that can be used by a supervisor agent.
"""

from typing import Any, Callable

from langchain.tools import ToolRuntime, tool

from agent.core.context import Context


def create_agent_handler(
    agent: Any,
    agent_name: str,
) -> Callable:
    """Create a tool-wrapped handler for an agent to be used in supervisor.

    Args:
        agent: Compiled LangChain agent (from create_agent)
        agent_name: Human-readable name for the agent

    Returns:
        Async callable tool function that invokes the agent
    """

    @tool
    async def agent_handler(
        query: str,
        runtime: ToolRuntime[Context],
    ) -> str:
        """Invoke a specialized agent to handle a query.

        Args:
            query: The user query to process
            runtime: Tool runtime with context and store access

        Returns:
            Agent's response as a formatted string
        """
        try:
            # Prepare config for agent execution
            config = {
                "configurable": {
                    "user_id": runtime.context.user_id,
                    "thread_id": runtime.context.thread_id,
                }
            }

            # Invoke agent with the query
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": query}]},
                config=config,
            )

            # Extract response from result
            if isinstance(result, dict):
                messages = result.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    if isinstance(last_msg, dict):
                        return last_msg.get("content", str(last_msg))
                    return (
                        str(last_msg.content)
                        if hasattr(last_msg, "content")
                        else str(last_msg)
                    )
                return str(result)

            return str(result)

        except Exception as e:
            error_msg = f"Error in {agent_name}: {str(e)}"
            return error_msg

    # Set the tool name and description
    agent_handler.name = agent_name.lower().replace(" ", "_")
    agent_handler.description = f"Delegate to {agent_name} for specialized handling"

    return agent_handler


__all__ = ["create_agent_handler"]
