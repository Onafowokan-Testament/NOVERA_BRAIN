"""Message handler for processing user messages with agent."""

from langchain_core.messages import HumanMessage
from telegram import Update
from telegram.ext import ContextTypes

from agent.supervisor_graph import instantiate_novera_orchestrator
from bot.handlers.base_handler import typing_effect
from settings.logger_config import logger

# Global agent instance
_agent = None


def get_agent():
    """Get or create agent instance.
    
    Returns:
        The orchestrator agent instance
    """
    global _agent
    if _agent is None:
        _agent = instantiate_novera_orchestrator()
    return _agent


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
        input_data = {"messages": [HumanMessage(content=user_message)]}

        async with typing_effect(context, chat_id):
            agent = get_agent()

            agent_config = {
                "configurable": {"thread_id": telegram_id, "user_id": telegram_id}
            }
            logger.info(f"Using config: {agent_config}")

            try:
                result = await agent.ainvoke(input_data, config=agent_config)
                logger.info(f"Agent result type: {type(result)}")
                logger.info(f"Agent result content: {result}")
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
                if isinstance(result, dict) and "messages" in result:
                    messages = result.get("messages", [])
                    if messages and hasattr(messages[-1], "content"):
                        content = str(messages[-1].content).strip()
                        if content:
                            await update.message.reply_text(f"{content}.")
                        else:
                            await update.message.reply_text(
                                "I received an empty response. Please try again! 🤔"
                            )
                    else:
                        await update.message.reply_text(
                            "I couldn't process the response properly. Please try again! 🤔"
                        )
                else:
                    await update.message.reply_text(f"{result}")
            except Exception as re:
                logger.error(f"Error processing result: {str(re)}")
                await update.message.reply_text(
                    "I had trouble processing the response. Please try again! 🤔"
                )

    except Exception as e:
        logger.error(f"Error in message_handler: {str(e)}")
        await update.message.reply_text("Oops, something went wrong. Please try again!")
