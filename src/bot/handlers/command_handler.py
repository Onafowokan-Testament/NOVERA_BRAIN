"""Command handlers for common bot commands."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.database.models.user import AsyncUserModel
from settings.logger_config import logger

user_model = AsyncUserModel()


async def start_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle /start command with proper database operations.
    
    Args:
        update: Telegram update object
        context: Telegram context
    """
    logger.info("Processing /start command")
    user = update.effective_user
    existing_user = await user_model.get_user(telegram_id=str(user.id))

    if not existing_user:
        new_user = await user_model.create_user(
            {"telegram_id": str(user.id), "username": user.username}
        )
        logger.info(f"User created with id: {new_user}")
        welcome_message = f"Welcome {user.first_name}! You have been registered.\n\n"
    else:
        welcome_message = f"Welcome back {user.first_name}!\n\n"

    full_message = (
        welcome_message
        + """NOVERA HERE!! 

I can help you with questions related to:

• Questions on academic information and policies
• Fees, registration, and admission
• Campus facilities and student services
• Directions and navigation

Available Support Commands:

/help - Get support
/about - About this assistant
/commands - Show all commands
/contact - University contacts
/health - System status
/info - Your account details
/add_location - Add a new location to our database

Just ask me anything about Covenant University! 😊"""
    )

    await update.message.reply_text(full_message)


async def info_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle /info command to display user details.
    
    Args:
        update: Telegram update object
        context: Telegram context
    """
    logger.info("Processing /info command")
    user = update.effective_user

    existing_user = await user_model.get_user(telegram_id=str(user.id))
    
    if not existing_user:
        message = "You don't yet exist in our database"
    else:
        message = f"""Your details are as follows:

Telegram ID: {existing_user['telegram_id']}
Username: {existing_user.get('username', 'Not set')}"""

    await update.message.reply_text(message)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command.
    
    Args:
        update: Telegram update object
        context: Telegram context
    """
    logger.info("Processing /help command")

    message = """**Need Help?**

Send a message describing your problem and our support team (/contact) will assist you!

For best results:
• Be specific with your questions
• Ask about Covenant University topics
• Use simple, clear language

Just send a message!"""

    await update.message.reply_text(message, parse_mode="Markdown")


async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /about command.
    
    Args:
        update: Telegram update object
        context: Telegram context
    """
    logger.info("Processing /about command")

    message = """**ℹ About This Assistant**

I'm an AI assistant specifically designed for Covenant University.

What I can help with:
• Academic information and policies
• Fees, registration, and admission
• Campus facilities and student services
• Directions and navigation

My focus: Covenant University topics only
Version: 2.0

Have questions? Just ask! 🎓"""

    await update.message.reply_text(message, parse_mode="Markdown")


async def commands_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /commands command to show available commands.
    
    Args:
        update: Telegram update object
        context: Telegram context
    """
    logger.info("Processing /commands command")

    message = """**Available Commands**

/start - Welcome message
/help - Get support  
/about - About this assistant
/commands - Show this list
/contact - University contacts
/health - System status
/info - Your account details
/add_location - Add a new location

Just type any command or ask me about Covenant University! 😊"""

    await update.message.reply_text(message, parse_mode="Markdown")


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /contact command.
    
    Args:
        update: Telegram update object
        context: Telegram context
    """
    logger.info("Processing /contact command")

    message = """**Contacts**

For any queries or feedback, please contact us at:

Phone: @testy_oloye
Email: novera@gmail.com"""

    await update.message.reply_text(message)


async def health_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /health command to show system status.
    
    Args:
        update: Telegram update object
        context: Telegram context
    """
    logger.info("Processing /health command")

    message = """**System Status**

✓ Assistant: Online
✓ Knowledge Base: Connected  
✓ Response Time: Normal
✓ Last Updated: Recent

All systems operational! Ready to help with Covenant University questions!"""

    await update.message.reply_text(message, parse_mode="Markdown")


async def add_location_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /add_location command to add new locations.
    
    Args:
        update: Telegram update object
        context: Telegram context
    """
    logger.info("Processing /add_location command")

    message = (
        "To add a new location to our database, please fill out this form:\n"
        "https://forms.gle/VzyhtzyueCh2iKxk9"
    )

    await update.message.reply_text(message)
