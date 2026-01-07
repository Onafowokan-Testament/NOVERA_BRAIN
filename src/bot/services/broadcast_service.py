"""Broadcast service - Business logic for messaging operations."""

from typing import Any

from telegram.error import TelegramError

from bot.database.repositories import UserRepository
from settings.logger_config import logger


class BroadcastResult:
    """Result of a broadcast operation."""

    def __init__(self, total: int, success: int, failed: int) -> None:
        """Initialize broadcast result.
        
        Args:
            total: Total users
            success: Successfully sent count
            failed: Failed count
        """
        self.total = total
        self.success = success
        self.failed = failed

    def to_message(self) -> str:
        """Convert result to user-friendly message.
        
        Returns:
            Formatted message string
        """
        return (
            f"Broadcast completed!\n"
            f"📊 Total users: {self.total}\n"
            f"✅ Successfully sent: {self.success}\n"
            f"❌ Failed: {self.failed}"
        )


class BroadcastService:
    """Service for broadcast operations."""

    def __init__(self) -> None:
        """Initialize broadcast service."""
        self.user_repository = UserRepository()

    async def broadcast_message(self, message: str, bot_send_func: Any) -> BroadcastResult:
        """Broadcast a message to all users.
        
        Args:
            message: Message to broadcast
            bot_send_func: Async function to send message (receives chat_id and text)
            
        Returns:
            BroadcastResult with statistics
            
        Raises:
            Exception: If broadcast operation fails critically
        """
        try:
            users = await self.user_repository.get_all()
            
            if not users:
                logger.warning("No users found for broadcast")
                return BroadcastResult(total=0, success=0, failed=0)

            logger.info(f"Starting broadcast to {len(users)} users")
            success_count = 0
            fail_count = 0

            # Send message to each user
            for user in users:
                try:
                    telegram_id = user.get("telegram_id")
                    if not telegram_id:
                        logger.error(f"User missing telegram_id: {user}")
                        fail_count += 1
                        continue

                    await bot_send_func(chat_id=telegram_id, text=message)
                    success_count += 1
                    logger.info(f"Broadcast sent to user {telegram_id}")

                except TelegramError as e:
                    fail_count += 1
                    logger.error(
                        f"Failed to send broadcast to {user.get('telegram_id', 'unknown')}: {str(e)}"
                    )
                    continue

            return BroadcastResult(total=len(users), success=success_count, failed=fail_count)

        except Exception as e:
            logger.error(f"Broadcast error: {str(e)}")
            raise
