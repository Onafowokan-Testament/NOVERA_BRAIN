from typing import Any

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from bot.handlers import (
    about_handler,
    add_location_handler,
    commands_handler,
    contact_handler,
    handle_user_message,
    health_handler,
    help_handler,
)
from bot.session_wrapper import get_info, handle_start_update
from settings.config import Settings
from settings.logger_config import logger


async def build_bot() -> Any:
    """Build and return telegram bot application"""
    Settings.validate_keys()

    try:
        app = ApplicationBuilder().token(Settings.BOT_TOKEN).build()
        app.add_handler(CommandHandler("help", help_handler))
        app.add_handler(CommandHandler("about", about_handler))
        app.add_handler(CommandHandler("commands", commands_handler))
        app.add_handler(CommandHandler("contact", contact_handler))
        app.add_handler(CommandHandler("health", health_handler))

        app.add_handler(CommandHandler("start", handle_start_update))
        app.add_handler(CommandHandler("info", get_info))
        # app.add_handler(CommandHandler("get_locations", get_direc
        # tions_handler))
        app.add_handler(CommandHandler("add_location", add_location_handler))

        app.add_handler(
            MessageHandler(filters.ALL & ~filters.COMMAND, handle_user_message)
        )
        await app.initialize()
        logger.info("Telegram bot built successfully")
        return app
    except Exception as e:
        logger.error(f"Failed to build bot: {str(e)}")
        raise
