"""QA Agent - Document retrieval and question answering.

Conversational retrieval system with adaptive query generation,
multi-provider support, and stateful context management.
"""

from .agent import initiate_qa_agent
from .schema import Configuration, State, InputState, IndexState

# Create the default graph instance
graph = initiate_qa_agent()

__all__ = [
    "graph",
    "initiate_qa_agent",
    "Configuration",
    "State",
    "InputState",
    "IndexState",
]
