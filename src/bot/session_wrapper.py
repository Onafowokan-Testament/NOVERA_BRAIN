from contextlib import asynccontextmanager
from typing import Any

from loguru import logger

from bot.database.database import db_connection
from bot.handlers import info_handler, start_handler

client = db_connection.client


@asynccontextmanager
async def get_db_session():
    try:
        client = await db_connection.client
        yield client
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")


async def handle_start_update(update: Any, context: Any):
    """Handle updates with database session"""
    async with get_db_session() as session:
        try:
            await start_handler(update, context)
        except Exception as e:
            logger.error(f"Error in start handler:{str(e)}")
            await update.message.reply_text(
                "OOps, something went wrong. Try again! 😂 "
            )


async def get_info(update, context):
    """Handles /get_info command in databasegetting user update"""
    async with get_db_session() as session:
        try:
            await info_handler(update, context)
        except Exception as e:
            logger.error(f"Error in info_handler : {str(e)}")
            await update.message.reply_text("Oops , something went wrong : str(e)")
