"""Broadcast handler for admin broadcast functionality."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.services import BroadcastService
from settings.config import Settings
from settings.logger_config import logger

broadcast_service = BroadcastService()


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcast a message to all registered users (admin only).
    
    Args:
        update: Telegram update object
        context: Telegram context
        
    Note:
        Only users with admin IDs can use this command.
    """
    # Check if user is admin
    admin_ids = getattr(Settings, 'ADMIN_IDS', [])
    
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text(
            "Sorry, this command is only available for admins."
        )
        return

    # Get the message to broadcast
    message_text = update.message.text.replace("/send_broadcast_message ", "")
    if not message_text:
        await update.message.reply_text(
            "Please provide a message to broadcast.\nUsage: /broadcast <message>"
        )
        return

    try:
        # Use service to broadcast
        result = await broadcast_service.broadcast_message(
            message=message_text,
            bot_send_func=context.bot.send_message
        )
        
        await update.message.reply_text(result.to_message())

    except Exception as e:
        logger.error(f"Broadcast error: {str(e)}")
        await update.message.reply_text(
            "An error occurred while broadcasting the message."
        )
