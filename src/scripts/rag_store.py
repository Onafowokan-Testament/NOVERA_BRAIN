import asyncio
import pprint
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import uuid4

from langchain_community.document_loaders import FileSystemBlobLoader
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import PyPDFParser, RapidOCRBlobParser
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from loguru import logger
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.http.models import Distance, VectorParams

from settings.config import Settings

Settings.validate_keys()


class RAGStore:
    def __init__(self, collection_name: str = "novera_handbook"):
        self.docs: List[Document] = []
        self.client: Optional[AsyncQdrantClient] = None
        self.collection_name = collection_name
        self.embedding = OpenAIEmbeddings(api_key=Settings.OPENAI_API_KEY)

    async def load_document(
        self,
        file_path: Path = Path("src/documents/handbook2.pdf"),
        file_type: str = "pdf",
    ) -> None:
        """Load and process document from file path"""
        if not file_path.exists():
            raise FileNotFoundError(f"❌File {file_path} does not exist")

        logger.info(f"File path{file_path} exist. Loading document")
        try:
            loader = GenericLoader(
                blob_loader=FileSystemBlobLoader(path=file_path, glob="*.pdf"),
                blob_parser=PyPDFParser(
                    images_inner_format="markdown-img",
                    images_parser=RapidOCRBlobParser(),
                ),
            )

            logger.info("Loading document ...")
            self.docs = await loader.aload()

            if self.docs:

                pprint.pp(self.docs[1:3])
        except Exception as e:
            logger.error(f"Error loading document {e}")
            raise

    def _get_client(self) -> AsyncQdrantClient:
        """Get or create Qdrant client."""
        if self.client is None:
            self.client = AsyncQdrantClient(
                api_key=Settings.QDRANT_API_KEY,
                url=Settings.QDRANT_API_ENDPOINT,
            )
        return self.client

    async def collection_exists(self) -> bool:
        """Check if collection exists."""
        try:
            client = self._get_client()
            collections = await client.get_collections()
            return any(
                col.name == self.collection_name for col in collections.collections
            )
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            return False

    async def create_collection(self, force_recreate: bool = False) -> None:

        client = self._get_client()

        try:
            exists = await self.collection_exists()

            if exists and force_recreate:
                logger.info(f"Deleting existing collection: {self.collection_name}")
                await client.delete_collection(self.collection_name)
                exists = False

            if not exists:
                logger.info(f"Creating collection: {self.collection_name}")
                await client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                )
                logger.info(f"✅ Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection {self.collection_name} already exists")

        except UnexpectedResponse as e:
            logger.error(f"Error creating collection: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating collection: {e}")
            raise

    async def add_vector_docs(self, batch_size: int = 100) -> None:
        """Add documents to vector store in batches."""
        if not self.docs:
            logger.warning("No documents loaded. Call load_document() first.")
            return

        try:
            # Ensure collection exists
            if not await self.collection_exists():
                await self.create_collection()

            qdrant = QdrantVectorStore.from_existing_collection(
                embedding=self.embedding,
                collection_name=self.collection_name,
                client=AsyncQdrantClient(
                    api_key=Settings.QDRANT_API_KEY, url=Settings.QDRANT_API_ENDPOINT
                ),
            )

            # Process in batches to avoid memory issues
            total_docs = len(self.docs)
            logger.info(f"Adding {total_docs} documents in batches of {batch_size}")

            for i in range(0, total_docs, batch_size):
                batch_docs = self.docs[i : i + batch_size]
                batch_uuids = [str(uuid4()) for _ in range(len(batch_docs))]

                logger.info(
                    f"Adding batch {i//batch_size + 1}/{(total_docs-1)//batch_size + 1}"
                )
                await qdrant.aadd_documents(documents=batch_docs, ids=batch_uuids)

            logger.info(f"✅ Successfully added {total_docs} documents to vector store")

        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise

    async def get_vector_store(self) -> QdrantVectorStore:
        """Get vector store instance."""
        try:
            logger.info(f"collection name: {self.collection_name }-------------")
            if not await self.collection_exists():
                raise ValueError(
                    f"Collection {self.collection_name} does not exist. Create it first."
                )

            logger.info("Getting vector store...")
            vectorstore = await asyncio.to_thread(
                QdrantVectorStore.from_existing_collection,
                embedding=self.embedding,
                collection_name=self.collection_name,
                url=Settings.QDRANT_API_ENDPOINT,
                api_key=Settings.QDRANT_API_KEY,
            )

            logger.info(f"✅ Retrieved vector store: {self.collection_name}")
            return vectorstore

        except Exception as e:
            logger.error(f"Error getting vector store: {e}")
            raise

    async def search(
        self, query: str, k: int = 5, score_threshold: float = 0.7
    ) -> List[Tuple[Document, float]]:
        """Search for similar documents with improved filtering."""
        try:
            vectorstore = await self.get_vector_store()
            results = vectorstore.similarity_search_with_relevance_scores(query, k=k)

            # Filter by score threshold
            filtered_results = [
                (doc, score) for doc, score in results if score >= score_threshold
            ]

            logger.info(
                f"Found {len(filtered_results)}/{len(results)} results above threshold {score_threshold}"
            )
            return filtered_results

        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            raise

    async def close(self) -> None:
        """Close the Qdrant client connection."""
        if self.client:
            self.client.close()
            logger.info("Closed Qdrant client connection")


async def main():
    """Main function demonstrating RAG store usage."""
    store = RAGStore()

    try:
        # Load document (uncomment to reload)
        # await store.load_document()
        # await store.create_collection(force_recreate=True)
        # await store.add_vector_docs()

        # Search for documents
        results = await store.search(query="what can i wear", k=5, score_threshold=0.5)

        if results:
            logger.info(f"Found {len(results)} relevant documents:")
            for i, (doc, score) in enumerate(results, 1):
                print(f"\n--- Result {i} (Score: {score:.3f}) ---")
                print(f"Content: {doc.page_content[:200]}...")
                print(f"Metadata: {doc.metadata}")
        else:
            logger.info("No relevant documents found")

    except Exception as e:
        logger.error(f"Error in main: {e}")

    finally:
        await store.close()


if __name__ == "__main__":
    asyncio.run(main())
