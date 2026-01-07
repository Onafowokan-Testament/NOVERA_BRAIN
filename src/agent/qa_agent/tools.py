"""QA Agent - Tool Definitions.

Tool definitions for QA agent including web search capabilities.
"""

from typing import Any, Callable, List, cast

from langchain_tavily import TavilySearch

from .schema import Configuration


async def web_search_tool(query: str):
    """Executes comprehensive internet queries through the Tavily search platform.
    This tool specializes in delivering reliable, up-to-date information and
    excels when addressing inquiries related to recent developments and current
       affairs. It should be used when retrieved document are sketchy
    """
    max_search_result = Configuration.max_search_results
    search = TavilySearch(
        max_results=max_search_result,
        time_range="year",
        include_domains=["https://covenantuniversity.edu.ng"],
    )
    return cast(dict[str, Any], await search.ainvoke({"query": query}))


TOOLS: List[Callable[..., Any]] = [web_search_tool]
