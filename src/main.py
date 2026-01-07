from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from settings.logger_config import logger   
from telegram import Update

from bot.database.database import db_connection
from bot.telegram_bot import build_bot


class BotManager:
    """Thread-safe bot manager for concurrency"""

    def __init__(self):
        self._bot = None

    async def initialize(self):
        """Initialize the bot"""
        if self._bot is None:
            self._bot = await build_bot()

    async def shutdown(self):
        """Shutdown the bot"""
        logger.info("Initiating bot shutdown")
        try:
            await self._bot.shutdown()
            logger.info("Bot shutdown completed successfully")
        except Exception as e:
            logger.error(f"Error during bot shutdown: {str(e)}")
        finally:
            self._bot = None

    @property
    def bot(self):
        """Get the bot instance"""
        if self._bot is None:
            raise RuntimeError("Bot not initialized")
        return self._bot


bot_manager = BotManager()


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("connecting to database")
    await db_connection.connect()
    logger.info("Successfully connected to database")

    logger.info("Starting up bot")
    await bot_manager.initialize()

    logger.info("✅ Bot and database ready!")
    yield
    logger.info("🛑 Shutting down bot...")
    await bot_manager.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def home():
    """Health check point"""
    return {"message": "Novera bot backend running successfully"}


@app.get("/health")
async def health_check():
    """Extended health check"""
    try:
        bot = bot_manager.bot
        return {"status": "healthy", "bot_initialized": bot is not None}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/webhook")
async def webhook_handler(
    request: Request,
):
    """Handle telegram webhook updates"""

    try:
        # Get bot instance safely
        bot_app = bot_manager.bot

        body = await request.json()
        if not body:
            raise HTTPException(status_code=400, detail="Empty request")

        update = Update.de_json(body, bot_app.bot)
        if not update:
            raise HTTPException(status_code=400, detail="Invalid update")

        await bot_app.process_update(update)
        logger.info(f"Processed webhook update: {update}")
        return {"ok": True}

    except RuntimeError as e:
        logger.error(f"Bot not ready: {str(e)}")
        raise HTTPException(status_code=503, detail="Bot not initialized")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in webhook handler: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
