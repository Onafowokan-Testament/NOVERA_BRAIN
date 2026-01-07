"""Manage the configuration of various retrievers.

This module provides functionality to create and manage retrievers for different
vector store backends, specifically Elasticsearch, Pinecone, and MongoDB.

The retrievers support filtering results by user_id to ensure data isolation between users.
"""

from contextlib import asynccontextmanager
from typing import Generator

from langchain_core.embeddings import Embeddings
from langchain_core.runnables import RunnableConfig
from langchain_core.vectorstores import VectorStoreRetriever

from scripts.rag_store import RAGStore

from .configuration import IndexConfiguration

## Encoder constructors


def make_text_encoder(model: str) -> Embeddings:
    """Connect to the configured text encoder."""
    provider, model = model.split("/", maxsplit=1)
    match provider:
        case "openai":
            from langchain_openai import OpenAIEmbeddings

            return OpenAIEmbeddings(model=model)

        case _:
            raise ValueError(f"Unsupported embedding provider: {provider}")


## Retriever constructors


@asynccontextmanager
async def make_qdrant_retriever(
    configuration: IndexConfiguration, embedding_model: Embeddings
) -> Generator[VectorStoreRetriever, None, None]:
    """Configure this agent to connect to a specific qdrant index."""

    search_kwargs = configuration.search_kwargs
    rag_store = RAGStore()
    vstore = await rag_store.get_vector_store()
    # vstore = QdrantVectorStore.from_existing_index(
    #     os.environ["PINECONE_INDEX_NAME"], embedding=embedding_model
    # )
    retriever = vstore.as_retriever(search_kwargs=search_kwargs)

    try:
        yield retriever
    finally:
        pass


@asynccontextmanager
async def make_retriever(
    config: RunnableConfig,
) -> Generator[VectorStoreRetriever, None, None]:
    """Create a retriever for the agent, based on the current configuration."""
    configuration = IndexConfiguration.from_runnable_config(config)
    embedding_model = make_text_encoder(configuration.embedding_model)
    async with make_qdrant_retriever(configuration, embedding_model) as retriever:
        yield retriever
