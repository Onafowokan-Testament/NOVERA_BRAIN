from typing import Annotated, List, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """state for novera supervisor"""

    messages: Annotated[List[AnyMessage], add_messages]
    memory: str
