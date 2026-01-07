"""QA Agent - Configuration, State, and Models.

Consolidated schema definitions for the QA agent including configuration,
state management, and models for document retrieval and question answering.
"""

import uuid
from dataclasses import dataclass, field, fields
from typing import Annotated, Any, Literal, Optional, Sequence, Type, TypeVar, Union

from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig, ensure_config
from langgraph.graph import add_messages

from . import prompts

# ============================================================================
# CONFIGURATION
# ============================================================================

T = TypeVar("T")


@dataclass(kw_only=True)
class IndexConfiguration:
    """Configuration for indexing and retrieval operations."""

    user_id: str = field(
        default="user1", metadata={"description": "Unique identifier for the user."}
    )

    embedding_model: Annotated[str, {"__template_metadata__": {"kind": "embeddings"}}] = field(
        default="openai/text-embedding-3-small",
        metadata={"description": "Name of the embedding model to use."},
    )

    retriever_provider: Annotated[
        Literal["elastic", "elastic-local", "pinecone", "mongodb", "qdrant"],
        {"__template_metadata__": {"kind": "retriever"}},
    ] = field(
        default="qdrant",
        metadata={"description": "Vector store provider for retrieval."},
    )

    search_kwargs: dict[str, Any] = field(
        default_factory=dict,
        metadata={"description": "Additional kwargs for retriever search."},
    )

    @classmethod
    def from_runnable_config(
        cls: Type[T], config: Optional[RunnableConfig] = None
    ) -> T:
        """Create IndexConfiguration from RunnableConfig."""
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})


@dataclass(kw_only=True)
class Configuration(IndexConfiguration):
    """Full configuration for QA agent."""

    response_system_prompt: str = field(
        default=prompts.RESPONSE_SYSTEM_PROMPT,
        metadata={"description": "System prompt for response generation."},
    )

    response_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/gpt-4o-mini",
        metadata={"description": "Language model for generating responses."},
    )

    max_search_results: int = field(
        default=5,
        metadata={"description": "Maximum search results to return."},
    )

    query_system_prompt: str = field(
        default=prompts.QUERY_SYSTEM_PROMPT,
        metadata={"description": "System prompt for query processing."},
    )

    query_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/gpt-4o-mini",
        metadata={"description": "Language model for query refinement."},
    )


# ============================================================================
# STATE - Helper Functions
# ============================================================================


def reduce_docs(
    existing: Optional[Sequence[Document]],
    new: Union[
        Sequence[Document],
        Sequence[dict[str, Any]],
        Sequence[str],
        str,
        Literal["delete"],
    ],
) -> Sequence[Document]:
    """Process and reduce documents."""
    if new == "delete":
        return []
    if isinstance(new, str):
        return [Document(page_content=new, metadata={"id": str(uuid.uuid4())})]
    if isinstance(new, list):
        coerced = []
        for item in new:
            if isinstance(item, str):
                coerced.append(
                    Document(page_content=item, metadata={"id": str(uuid.uuid4())})
                )
            elif isinstance(item, dict):
                coerced.append(Document(**item))
            else:
                coerced.append(item)
        return coerced
    return existing or []


def add_queries(existing: Sequence[str], new: Sequence[str]) -> Sequence[str]:
    """Combine existing and new queries."""
    return list(existing) + list(new)


# ============================================================================
# STATE - Classes
# ============================================================================


@dataclass(kw_only=True)
class IndexState:
    """State for document indexing operations."""

    docs: Annotated[Sequence[Document], reduce_docs]
    """Documents to be indexed."""


@dataclass(kw_only=True)
class InputState:
    """Input state for the agent."""

    messages: Annotated[Sequence[AnyMessage], add_messages]
    """Conversation messages with message merging."""


@dataclass(kw_only=True)
class State(InputState):
    """Full graph state for QA agent."""

    queries: Annotated[list[str], add_queries] = field(default_factory=list)
    """Search queries generated by the agent."""

    retrieved_docs: list[Document] = field(default_factory=list)
    """Documents retrieved for reference."""


__all__ = [
    "Configuration",
    "IndexConfiguration",
    "IndexState",
    "InputState",
    "State",
    "reduce_docs",
    "add_queries",
]
