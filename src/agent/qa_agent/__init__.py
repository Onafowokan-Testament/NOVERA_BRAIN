"""QA Agent - Handles document retrieval and question answering.

This module provides a conversational retrieval graph system that enables
intelligent document retrieval and question answering based on user inputs.

Key Features:
- Adaptive query generation for improved document retrieval
- Integration with various retrieval providers (e.g., Elastic, Pinecone, MongoDB)
- Customizable language models for query and response generation
- Stateful conversation management for context-aware interactions
"""

from .graph import initiate_qa_agent

# Create the default graph instance
graph = initiate_qa_agent()

__all__ = ["graph", "initiate_qa_agent"]

