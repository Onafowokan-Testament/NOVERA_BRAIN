"""QA Agent - Tool Definitions.

Tool definitions for QA agent including web search and memory management.
Uses AWADOC pattern with @tool decorator and ToolRuntime[Context].
"""

from typing import Any, Callable, List, cast

from langchain.tools import ToolRuntime, tool
from langchain_tavily import TavilySearch

from agent.core.context import Context
from .schema import Configuration


@tool
async def web_search_tool(
    query: str,
    runtime: ToolRuntime[Context],
) -> str:
    """Executes comprehensive internet queries through the Tavily search platform.
    
    This tool specializes in delivering reliable, up-to-date information and
    excels when addressing inquiries related to recent developments and current
    affairs. Use when retrieved documents are sketchy or need current information.
    
    Args:
        query: The search query to execute
        runtime: Tool runtime with access to user context and store
        
    Returns:
        Search results formatted as a string
    """
    max_search_result = Configuration.max_search_results
    search = TavilySearch(
        max_results=max_search_result,
        time_range="year",
        include_domains=["https://covenantuniversity.edu.ng"],
    )
    results = cast(dict[str, Any], await search.ainvoke({"query": query}))
    return str(results)


@tool
async def save_qa_memory(
    query: str,
    answer: str,
    runtime: ToolRuntime[Context],
) -> str:
    """Save a question-answer pair to memory for future reference.
    
    Args:
        query: The question asked
        answer: The answer provided
        runtime: Tool runtime with access to user context and store
        
    Returns:
        Confirmation message
    """
    if runtime.store:
        user_id = runtime.context.user_id
        namespace = "qa"
        memory_key = (user_id, namespace, "qa_memory")
        
        memory_value = f"Q: {query}\nA: {answer}"
        await runtime.store.aput(
            memory_key,
            value=memory_value,
            namespace=namespace,
        )
        return f"Memory saved: {query[:50]}..."
    return "No store available for memory saving"


TOOLS: List[Callable[..., Any]] = [web_search_tool, save_qa_memory]
