"""Message handler for processing user messages with agent."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.base_handler import typing_effect
from bot.services import AgentService
from settings.logger_config import logger

# Initialize service
agent_service = AgentService()


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle general user messages with agent processing.
    
    Args:
        update: Telegram update object
        context: Telegram context
    """
    user_message = update.message.text.strip()
    if not user_message:
        logger.warning("Empty message received")
        await update.message.reply_text("Please send a message to get a response!")
        return

    telegram_id = str(update.effective_user.id)
    chat_id = update.message.chat_id

    try:
        async with typing_effect(context, chat_id):
            try:
                result = await agent_service.process_message(
                    message=user_message,
                    telegram_id=telegram_id
                )
                logger.info(f"Agent result received: {type(result)}")
            except TypeError as te:
                logger.error(f"TypeError in agent invocation: {str(te)}")
                await update.message.reply_text(
                    "I encountered a processing error. Please try rephrasing your question! 🤔"
                )
                return
            except Exception as ae:
                logger.error(f"Agent invocation error: {str(ae)}")
                await update.message.reply_text(
                    "I'm having trouble processing your request right now. Please try again! 🤔"
                )
                return

        if not result:
            logger.warning("Empty response from workflow")
            await update.message.reply_text(
                "Hmm, I couldn't generate a response. Try again! 🤔"
            )
        else:
            try:
                content = agent_service.extract_response_content(result)
                if content:
                    await update.message.reply_text(f"{content}.")
                else:
                    await update.message.reply_text(
                        "I received an empty response. Please try again! 🤔"
                    )
            except ValueError as ve:
                logger.error(f"Error extracting response: {str(ve)}")
                await update.message.reply_text(
                    "I had trouble processing the response. Please try again! 🤔"
                )
            except Exception as re:
                logger.error(f"Error processing result: {str(re)}")
                await update.message.reply_text(
                    "I had trouble processing the response. Please try again! 🤔"
                )

    except Exception as e:
        logger.error(f"Error in message_handler: {str(e)}")
        await update.message.reply_text("Oops, something went wrong. Please try again!")
