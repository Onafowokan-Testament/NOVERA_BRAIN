"""User service - Business logic for user operations."""

from typing import Any, Optional

from bot.database.repositories import UserRepository
from settings.logger_config import logger


class UserService:
    """Service for user-related operations."""

    def __init__(self) -> None:
        """Initialize user service."""
        self.user_repository = UserRepository()

    async def create_user_if_new(self, telegram_id: str, username: Optional[str] = None) -> tuple[bool, str]:
        """Create user if not exists.
        
        Args:
            telegram_id: Telegram user ID
            username: Optional username
            
        Returns:
            Tuple of (is_new: bool, user_id: str)
        """
        try:
            existing_user = await self.user_repository.get_by_telegram_id(telegram_id)
            
            if existing_user:
                logger.info(f"User {telegram_id} already exists")
                return False, str(existing_user.get("_id", telegram_id))
            
            new_user_id = await self.user_repository.create(
                {"telegram_id": telegram_id, "username": username}
            )
            logger.info(f"User {telegram_id} created with id: {new_user_id}")
            return True, new_user_id
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    async def get_user(self, telegram_id: str) -> Optional[dict[str, Any]]:
        """Get user by telegram ID.
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            User dict or None if not found
        """
        try:
            return await self.user_repository.get_by_telegram_id(telegram_id)
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            raise

    async def get_all_users(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get all users.
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of user dicts
        """
        try:
            return await self.user_repository.get_all(limit=limit)
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            raise

    async def user_exists(self, telegram_id: str) -> bool:
        """Check if user exists.
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            True if user exists, False otherwise
        """
        try:
            return await self.user_repository.exists_by_telegram_id(telegram_id)
        except Exception as e:
            logger.error(f"Error checking user existence: {e}")
            raise
