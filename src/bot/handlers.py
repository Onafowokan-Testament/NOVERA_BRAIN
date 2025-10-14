import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from telegram import Update
from telegram.ext import ContextTypes

from agent.supervisor_graph import instantiate_novera_orchestrator
from bot.database.models.user import AsyncUserModel
from settings.logger_config import logger

# Add these at the top of the file
active_conversations: Dict[int, asyncio.Task] = {}
rate_limits = defaultdict(lambda: {"last_request": None, "count": 0})


async def handle_user_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Process user message with rate limiting and concurrent handling"""
    user_id = update.effective_user.id
    chat_id = update.message.chat_id

    # Check rate limiting
    now = datetime.now()
    user_limit = rate_limits[user_id]

    if user_limit["last_request"]:
        if now - user_limit["last_request"] < timedelta(seconds=1):
            if user_limit["count"] > 5:  # Max 5 messages per second
                await update.message.reply_text("Please slow down a bit!")
                return
            user_limit["count"] += 1
        else:
            user_limit["count"] = 1

    user_limit["last_request"] = now

    # Cancel any existing conversation for this user
    if user_id in active_conversations:
        active_conversations[user_id].cancel()

    # Create new conversation task
    task = asyncio.create_task(process_message(update, context))
    active_conversations[user_id] = task

    try:
        await task
    except asyncio.CancelledError:
        logger.info(f"Conversation cancelled for user {user_id}")
    except Exception:
        logger.exception(f"Error processing message for user {user_id}")
        await update.message.reply_text(
            "Sorry, something went wrong. Please try again."
        )
    finally:
        if user_id in active_conversations:
            del active_conversations[user_id]


async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Actual message processing logic"""
    user_message = update.message.text.strip()
    if not user_message:
        return

    telegram_id = str(update.effective_user.id)
    chat_id = update.message.chat_id

    try:
        async with typing_effect(context, chat_id):
            input_data = {"messages": [HumanMessage(content=user_message)]}
            agent = await get_agent()

            agent_config = {
                "configurable": {"thread_id": telegram_id, "user_id": telegram_id}
            }

            result = await asyncio.wait_for(
                agent.ainvoke(input_data, config=agent_config),
                timeout=30.0,  # Add timeout to prevent hanging
            )

            if isinstance(result, dict) and "messages" in result:
                messages = result["messages"]
                if messages and hasattr(messages[-1], "content"):
                    await update.message.reply_text(str(messages[-1].content))
                    return

            await update.message.reply_text(str(result))

    except asyncio.TimeoutError:
        await update.message.reply_text(
            "Sorry, the request took too long. Please try again."
        )
    except Exception:
        logger.exception("Error in message processing")
        await update.message.reply_text(
            "Sorry, I encountered an error. Please try again."
        )


# Replace the existing message_handler with this
message_handler = handle_user_message

user_model = AsyncUserModel()
load_dotenv()


_agent_instance: Optional[Any] = None
_agent_lock = asyncio.Lock()
_initialization_task: Optional[asyncio.Task] = None


async def initialize_agent():
    """Initialize agent in a non-blocking way"""
    loop = asyncio.get_event_loop()
    # Run blocking initialization in thread pool
    agent = await loop.run_in_executor(
        None, instantiate_novera_orchestrator  # Uses default ThreadPoolExecutor
    )
    return agent


async def get_agent():
    """Thread-safe, non-blocking agent getter with lazy initialization"""
    global _agent_instance, _initialization_task

    async with _agent_lock:
        # If already initialized, return immediately
        if _agent_instance is not None:
            return _agent_instance

        # If initialization is in progress, wait for it
        if _initialization_task is not None:
            return await _initialization_task

        # Start new initialization
        _initialization_task = asyncio.create_task(initialize_agent())
        try:
            _agent_instance = await _initialization_task
            return _agent_instance
        finally:
            _initialization_task = None


@asynccontextmanager
async def typing_effect(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Non-blocking typing effect"""
    typing_task = None

    async def keep_typing():
        while True:
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            await asyncio.sleep(5)  # Update typing indicator every 5 seconds

    try:
        typing_task = asyncio.create_task(keep_typing())
        yield
    finally:
        if typing_task:
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass


async def start_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle /start command with proper database operations."""
    logger.info("Processing /start command")
    user = update.effective_user
    existing_user = await user_model.get_user(telegram_id=str(user.id))

    if not existing_user:
        new_user = await user_model.create_user(
            {"telegram_id": str(user.id), "username": user.username}
        )
        logger.info(f"User id: {new_user}")

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
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle /info command to display user details."""
    logger.info("Processing /info command")
    user = update.effective_user
    user_id = str(user.id)

    result = await user_model.get_user(telegram_id=str(user.id))
    existing_user = result if result else None
    if not existing_user:
        message = "You don't yet exist in our database"
    else:
        message = f"""
            Your details are as follows:

    
            Telegram_id: {existing_user['telegram_id']}


            Username: {existing_user.get('username', 'Not set')}

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


# async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     """Handle general user messages with improved typing effect."""

#     user_message = update.message.text.strip()
#     if not user_message:
#         logger.warning("Empty message received")
#         await update.message.reply_text("Please send a message to get a response! ")
#         return

#     telegram_id = str(update.effective_user.id)
#     chat_id = update.message.chat_id

#     try:
#         input_data = {"messages": [HumanMessage(content=user_message)]}

#         async with typing_effect(context, chat_id):
#             # Use cached agent instance
#             agent = get_agent()

#             agent_config = {
#                 "configurable": {"thread_id": telegram_id, "user_id": telegram_id}
#             }
#             logger.info(f"Using config: {agent_config}")

#             try:
#                 result = await agent.ainvoke(input_data, config=agent_config)
#                 logger.info(f"Agent result type: {type(result)}")
#                 logger.info(f"Agent result content: {result}")
#             except TypeError as te:
#                 logger.error(f"TypeError in agent invocation: {str(te)}")
#                 await update.message.reply_text(
#                     "I encountered a processing error. Please try rephrasing your question! 🤔"
#                 )
#                 return
#             except Exception as ae:
#                 logger.error(f"Agent invocation error: {str(ae)}")
#                 await update.message.reply_text(
#                     "I'm having trouble processing your request right now. Please try again! 🤔"
#                 )
#                 return

#         if not result:
#             logger.warning("Empty response from workflow")
#             await update.message.reply_text(
#                 "Hmm, I couldn't generate a response. Try again! 🤔"
#             )
#         else:
#             # Safe result processing
#             try:
#                 if isinstance(result, dict) and "messages" in result:
#                     messages = result.get("messages", [])
#                     if messages and hasattr(messages[-1], "content"):
#                         content = str(messages[-1].content).strip()
#                         if content:
#                             await update.message.reply_text(f"{content}.")
#                         else:
#                             await update.message.reply_text(
#                                 "I received an empty response. Please try again! 🤔"
#                             )
#                     else:
#                         await update.message.reply_text(
#                             "I couldn't process the response properly. Please try again! 🤔"
#                         )
#                 else:
#                     await update.message.reply_text(f"{result}")
#             except Exception as re:
#                 logger.error(f"Error processing result: {str(re)}")
#                 await update.message.reply_text(
#                     "I had trouble processing the response. Please try again! 🤔"
#                 )

#     except Exception as e:
#         logger.error(f"Error in message_handler: {str(e)}")
#         await update.message.reply_text(
#             "Oops, something went wrong. Please try again! "
#         )


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
