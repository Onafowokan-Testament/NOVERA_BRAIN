"""Base repository class with common database operations."""

from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Base repository class for database operations.

    This abstract class defines the interface for all repository implementations.
    """

    @abstractmethod
    async def get_by_id(self, id_: str) -> Optional[T]:
        """Get an entity by ID.

        Args:
            id_: Entity ID

        Returns:
            Entity or None if not found
        """
        pass

    @abstractmethod
    async def get_all(self, limit: int = 100) -> list[T]:
        """Get all entities.

        Args:
            limit: Maximum number of entities to return

        Returns:
            List of entities
        """
        pass

    @abstractmethod
    async def create(self, data: dict[str, Any]) -> str:
        """Create a new entity.

        Args:
            data: Entity data

        Returns:
            Created entity ID
        """
        pass

    @abstractmethod
    async def update(self, id_: str, data: dict[str, Any]) -> bool:
        """Update an entity.

        Args:
            id_: Entity ID
            data: Updated data

        Returns:
            True if updated, False otherwise
        """
        pass

    @abstractmethod
    async def delete(self, id_: str) -> bool:
        """Delete an entity.

        Args:
            id_: Entity ID

        Returns:
            True if deleted, False otherwise
        """
        pass
