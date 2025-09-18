import asyncio
import json
from typing import Annotated, Any, Callable, List, Optional, cast

from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from langchain_tavily import TavilySearch
from langgraph.utils.config import get_store
from loguru import logger

from .configuration import NoveraConfig


async def web_search_tool(query: str) -> Optional[dict[str, Any]]:
    """Executes comprehensive internet queries through the Tavily search platform.
    This tool specializes in delivering reliable, up-to-date information and
    excels when addressing inquiries related to recent developments and current
       affairs.
    """
    configuration = NoveraConfig.from_context()
    search = TavilySearch(max_results=configuration.max_search_results)
    return cast(dict[str, Any], await search.ainvoke({"query": query}))


async def user_profile_builder(
    query: str,
    context: str,
    key: str,
    config: Annotated[InjectedToolArg, RunnableConfig],
):
    """Generates profile for user from the conversation. Provides user input and context


    Args:

    query: The  main memory content. For example "user studies CSC213"
    context: Auguments the memory e.g "This was mentioned when asking for location"
    key: memory to create or overwrite
    """
    store = get_store()
    user_id = NoveraConfig.from_runnables().user_id

    store = get_store()

    store.aput(
        ("memories", user_id, "user_profile"),
        key=key,
        value={"content": query, context: context},
    )
    return query


async def store_user_profile(message: BaseMessage, config: RunnableConfig):
    tool_calls = message.tool_calls

    logger.info(f"Tool calls: {tool_calls}")

    saved_memories = await asyncio.gather(
        *(_process_tool_call(tc, config=config) for tc in tool_calls)
    )

    results = [
        {"role": "tool", "content": json.dumps(mem), "tool_call_id": tc["id"]}
        for tc, mem in zip(tool_calls, saved_memories)
    ]

    return {"messages": results}


async def _process_tool_call(tool_call, config: RunnableConfig):
    args = tool_call["args"]

    if isinstance(args, str):
        args = json.loads(args)

    result = await user_profile_builder(**args, config=config)
    return result


TOOLS: List[Callable[..., Any]] = [web_search_tool]
