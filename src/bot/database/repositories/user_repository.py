"""User repository - Data access layer for user operations."""

from typing import Any, Optional

from bson import ObjectId

from bot.database.database import db_connection
from bot.database.repositories.base_repository import BaseRepository
from settings.logger_config import logger


class UserRepository(BaseRepository):
    """Repository for user data access."""

    def __init__(self) -> None:
        """Initialize user repository."""
        self.collection_name = "users"

    async def _get_collection(self) -> Any:
        """Get the users collection.

        Returns:
            MongoDB collection
        """
        return db_connection.database[self.collection_name]

    async def get_by_id(self, id_: str) -> Optional[dict[str, Any]]:
        """Get user by MongoDB ID.

        Args:
            id_: User MongoDB ID

        Returns:
            User dict or None if not found
        """
        try:
            collection = await self._get_collection()
            return await collection.find_one({"_id": ObjectId(id_)})
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None

    async def get_by_telegram_id(self, telegram_id: str) -> Optional[dict[str, Any]]:
        """Get user by telegram ID.

        Args:
            telegram_id: Telegram user ID

        Returns:
            User dict or None if not found
        """
        try:
            collection = await self._get_collection()
            return await collection.find_one({"telegram_id": telegram_id})
        except Exception as e:
            logger.error(f"Error getting user by telegram ID: {e}")
            return None

    async def get_all(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get all users.

        Args:
            limit: Maximum number of users to return

        Returns:
            List of user dicts
        """
        try:
            collection = await self._get_collection()
            cursor = collection.find({})
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []

    async def create(self, data: dict[str, Any]) -> str:
        """Create a new user.

        Args:
            data: User data

        Returns:
            Created user ID
        """
        try:
            collection = await self._get_collection()
            result = await collection.insert_one(data)
            logger.info(f"User created with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    async def update(self, id_: str, data: dict[str, Any]) -> bool:
        """Update a user.

        Args:
            id_: User MongoDB ID
            data: Updated user data

        Returns:
            True if updated, False otherwise
        """
        try:
            collection = await self._get_collection()
            result = await collection.update_one({"_id": ObjectId(id_)}, {"$set": data})
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False

    async def delete(self, id_: str) -> bool:
        """Delete a user.

        Args:
            id_: User MongoDB ID

        Returns:
            True if deleted, False otherwise
        """
        try:
            collection = await self._get_collection()
            result = await collection.delete_one({"_id": ObjectId(id_)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False

    async def exists_by_telegram_id(self, telegram_id: str) -> bool:
        """Check if user exists by telegram ID.

        Args:
            telegram_id: Telegram user ID

        Returns:
            True if exists, False otherwise
        """
        try:
            user = await self.get_by_telegram_id(telegram_id)
            return user is not None
        except Exception as e:
            logger.error(f"Error checking user existence: {e}")
            return False
