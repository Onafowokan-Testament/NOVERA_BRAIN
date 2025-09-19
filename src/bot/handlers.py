import asyncio
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from telegram import Update
from telegram.ext import ContextTypes

from agent.supervisor_graph import instantiate_novera_orchestrator
from bot.database.models.user import AsyncUserModel

user_model = AsyncUserModel()
load_dotenv()


@asynccontextmanager
async def typing_effect(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Context manager to show continuous typing effect during processing."""
    typing_task = None

    async def keep_typing():
        """Continuously send typing action every 4 seconds."""
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


async def start_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncIOMotorClient
) -> None:
    """Handle /start command with proper database operations."""
    logger.info("Processing /start command")
    user = update.effective_user
    result = await user_model.get_user(telegram_id=str(user.id))
    existing_user = result.scalar_one_or_none()

    if not existing_user:
        new_user = await user_model.create_user(
            {"telegram_id": str(user.id), "username": user.username}
        )

        welcome_message = f"Welcome {user.first_name}! You have been registered.\n\n"
    else:
        welcome_message = f"Welcome back {user.first_name}!\n\n"

    # Add the full start message
    full_message = (
        welcome_message
        + """ NOVERA HERE!! 

I can help you with questions related to:

• Questions on:


• Academic information and policies

• Fees, registration, and admission

• Campus facilities and student services


• Directions and navigation


Available Support  Commands:

/help - Get support
/about - About this assistant
/commands - Show all commands
/contact - University contacts
/health - System status
/info  - Your account details
/add_location - Add a new location to our database
/get_locations - Get the locations we have currently  

Just ask me anything about Covenant University! 😊"""
    )

    await update.message.reply_text(full_message)


async def info_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session: AsyncIOMotorClient
) -> None:
    """Handle /info command to display user details."""
    logger.info("Processing /info command")
    user = update.effective_user
    user_id = str(user.id)

    existing_user = await user_model.get_user(telegram_id=str(user.id))

    if not existing_user:
        message = "You don't yet exist in our database"
    else:
        message = f"""
            Your details are as follows:

    

            Telegram_id: {existing_user.telegram_id}

            Username: {existing_user.username}

        """

    await update.message.reply_text(message)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    logger.info("Processing /help command")

    message = """Need Help? **

Send a message describing your problem and our support team (/contact) will assist you!

For best results:
• Be specific with your questions
• Ask about Covenant University topics
• Use simple, clear language

Just send a message! """

    await update.message.reply_text(message, parse_mode="Markdown")


async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /about command"""
    logger.info("Processing /about command")

    message = """ℹ **About This Assistant**

I'm an AI assistant specifically designed for Covenant University.

What I can help with:

Questions on:


• Academic information and policies

• Fees, registration, and admission

• Campus facilities and student services

• Directions and navigation


My focus: Covenant University topics only
Version: 2.0

Have questions? Just ask! 🎓"""

    await update.message.reply_text(message, parse_mode="Markdown")


async def commands_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /commands command"""
    logger.info("Processing /commands command")

    message = """ Available Commands

/start - Welcome message
/help - Get support  
/about - About this assistant
/commands - Show this list
/contact - University contacts
/health - System status
/info - Your account details

Just type any command or ask me about Covenant University! 😊"""

    await update.message.reply_text(message, parse_mode="Markdown")


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /contact command"""
    logger.info("Processing /contact command")

    message = """ Contacts

For any queries or feedback, please contact us at:

Phone: @testy_oloye

Email: novera@gmail.com


"""

    await update.message.reply_text(message)


async def health_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /health command"""
    logger.info("Processing /health command")

    message = """System Status

Assistant: Online

Knowledge Base: Connected  

Response Time: Normal

Last Updated: Recent

All systems operational! Ready to help with Covenant University questions! """

    await update.message.reply_text(message, parse_mode="Markdown")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle general user messages with imnproved typing effect."""

    agent = instantiate_novera_orchestrator()

    user_message = update.message.text.strip()
    if not user_message:
        logger.warning("Empty message received")
        await update.message.reply_text("Please send a message to get a response! ")
        return

    telegram_id = str(update.effective_user.id)
    chat_id = update.message.chat_id

    try:
        # # agent.build_graph()
        # if not agent.workflow:
        #     logger.info("Building workflow")
        #     await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        #     print('#############################')
        #     agent.build_graph()

        input_data = {"messages": HumanMessage(content=user_message)}

        async with typing_effect(context, chat_id):

            agent_config = {"configurable": {"thread_id": telegram_id}}
            result = await agent.ainvoke(config=agent_config, initial_state=input_data)

        if not result:
            logger.warning("Empty response from workflow")
            await update.message.reply_text(
                "Hmm, I couldn't generate a response. Try again! 🤔"
            )
        else:
            await update.message.reply_text(f"{result['messages'][-1].content}.")

    except Exception as e:
        logger.error(f"Error in message_handler: {str(e)}")
        await update.message.reply_text(
            "Oops, something went wrong. Please try again! "
        )


async def add_location_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /add_location command to add new locations."""
    logger.info("Processing /add_location command")

    message = (
        "To add a new location to our database, please fill out this form:\n"
        "https://forms.gle/VzyhtzyueCh2iKxk9"
    )

    await update.message.reply_text(message)


# async def get_directions_handler(
#     update: Update, context: ContextTypes.DEFAULT_TYPE
# ) -> None:
#     """Handle /get_locations to get the directions we have currently."""
#     logger.info("Processing /get_direction_handler command")

#     directions = "\n\n".join(data.get("directions", {}))
#     message = f"""These are the current directions we have at the moment

#       {directions}
#         """

#     await update.message.reply_text(message)
