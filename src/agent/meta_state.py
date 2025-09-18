from typing import Annotated, List, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt.chat_agent_executor import AgentState

class OrchestrationState(AgentState):
    """state for novera supervisor"""

    messages: Annotated[List[AnyMessage], add_messages]
    memory: str
