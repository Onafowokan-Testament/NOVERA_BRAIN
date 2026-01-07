"""Base handler with common functionality."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from telegram.ext import ContextTypes

from settings.logger_config import logger


@asynccontextmanager
async def typing_effect(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> AsyncGenerator[None, None]:
    """Context manager to show continuous typing effect during processing.
    
    Args:
        context: Telegram context
        chat_id: Chat ID to show typing action in
        
    Yields:
        None
    """
    typing_task = None

    async def keep_typing() -> None:
        """Continuously send typing action every 3 seconds."""
        while True:
            try:
                await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                await asyncio.sleep(3)
            except Exception as e:
                logger.error(f"Error sending typing action: {e}")
                break

    try:
        typing_task = asyncio.create_task(keep_typing())
        yield
    finally:
        if typing_task and not typing_task.done():
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass
