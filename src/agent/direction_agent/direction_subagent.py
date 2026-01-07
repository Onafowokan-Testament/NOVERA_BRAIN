"""Direction Agent - AWADOC Pattern with Memory Management."""

import asyncio
import json
from datetime import datetime
from typing import cast

from decouple import config
from langchain.chat_models import init_chat_model
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.store.base import BaseStore

from agent.core.state import MemoryNamespace
from settings.logger_config import logger

from .configuration import Configuration
from .prompts import SYSTEM_PROMPT
from .state import State
from .tools import TOOLS, process_tool_call

# Initialize the language model to be used for memory extraction
llm = init_chat_model(model="gpt-4o-mini", model_provider="openai")
AGENT_NAME: str = config("DIRECTION_AGENT_NAME", default="direction_agent")


async def call_model(state: State, config: RunnableConfig, *, store: BaseStore) -> dict:
    """Extract the user's state from the conversation and update the memory."""
    configurable = Configuration.from_runnable_config(config)

    user_id = configurable.user_id
    model = configurable.model

    logger.info(f"Direction Agent - User ID: {user_id}")

    # Retrieve the most recent memories for context using direction-specific namespace
    memories = await cast(BaseStore, store).asearch(
        (MemoryNamespace.DIRECTION.value, user_id),
        query=str([m.content for m in state.messages[-3:]]),
        limit=10,
    )

    # Format memories for inclusion in the prompt
    formatted = "\n".join(
        f"[{mem.key}]: {mem.value} (relevance: {mem.score:.2f})" for mem in memories
    )
    if formatted:
        formatted = f"""
<relevant_memories>
{formatted}
</relevant_memories>"""

    # Prepare the system prompt with user memories and current time
    sys = SYSTEM_PROMPT.format(time=datetime.now().isoformat(), memories=formatted)

    # Invoke the language model with the prepared prompt and tools
    msg = await llm.bind_tools(TOOLS).ainvoke(
        [{"role": "system", "content": sys}, *state.messages],
    )

    if hasattr(msg, "name") and msg.name is None:
        msg.name = AGENT_NAME

    logger.info(
        f"Direction Agent Response: {msg.content if hasattr(msg, 'content') else msg}"
    )
    return {"messages": [msg]}


async def store_memory(state: State, config: RunnableConfig, *, store: BaseStore):
    """Store direction-related memories from tool calls."""
    # Extract tool calls from the last message
    tool_calls = state.messages[-1].tool_calls

    for tc in tool_calls:
        logger.debug(f"Processing tool call: {tc.get('name')}")

    # Concurrently execute all memory storage operations
    saved_memories = await asyncio.gather(
        *(
            process_tool_call(
                tc,
                config=config,
                store=store,
                namespace=MemoryNamespace.DIRECTION,
            )
            for tc in tool_calls
        )
    )

    # Format the results of memory storage operations
    results = [
        {
            "role": "tool",
            "content": json.dumps(mem),
            "tool_call_id": tc["id"],
        }
        for tc, mem in zip(tool_calls, saved_memories)
    ]
    logger.info(f"Stored {len(results)} direction memories")
    return {"messages": results}


def route_message(state: State):
    """Determine the next step based on the presence of tool calls."""
    msg = state.messages[-1]
    if getattr(msg, "tool_calls", None):
        # If there are tool calls, we need to store memories
        return "store_memory"
    # Otherwise, finish; user can send the next message
    return END


def initiate_direction_agent(agent_name=None):
    # Create the graph + all nodes

    if agent_name is None:
        agent_name = AGENT_NAME
    builder = StateGraph(State, config_schema=Configuration)

    # Define the flow of the memory extraction process
    builder.add_node(call_model)
    builder.add_edge("__start__", "call_model")
    builder.add_node(store_memory)
    builder.add_conditional_edges("call_model", route_message, ["store_memory", END])
    # Right now, we're returning control to the user after storing a memory
    # Depending on the model, you may want to route back to the model
    # to let it first store memories, then generate a response
    builder.add_edge("store_memory", "call_model")
    return builder.compile(name=agent_name)
