"""Broadcast handler for admin broadcast functionality."""

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from bot.database.models.user import AsyncUserModel
from settings.config import Settings
from settings.logger_config import logger

user_model = AsyncUserModel()


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
        users = await user_model.get_users()
        if not users:
            await update.message.reply_text("No users found in the database.")
            return

        logger.info(f"Found {len(users)} users to broadcast to")
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

                await context.bot.send_message(chat_id=telegram_id, text=message_text)
                success_count += 1
                logger.info(f"Successfully sent broadcast to user {telegram_id}")

            except TelegramError as e:
                fail_count += 1
                logger.error(
                    f"Failed to send broadcast to user {user.get('telegram_id', 'unknown')}: {str(e)}"
                )
                continue

        status_message = (
            f"Broadcast completed!\n"
            f"📊 Total users: {len(users)}\n"
            f"✅ Successfully sent: {success_count}\n"
            f"❌ Failed: {fail_count}"
        )
        await update.message.reply_text(status_message)

    except Exception as e:
        logger.error(f"Broadcast error: {str(e)}")
        await update.message.reply_text(
            "An error occurred while broadcasting the message."
        )
