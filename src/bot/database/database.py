import asyncio
from typing import Optional

from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from settings.config import Settings

Settings.validate_keys()


class DatabaseConnection:
    """Singleton MongoDB connection manager"""

    _instance = None
    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    async def client(self):
        if self._client is None:
            logger.info("Connecting to database first")
            try:
                await self.connect()
            except RuntimeError:
                raise RuntimeError("Database not connected . call connect () first")

        return self._client

    @property
    def database(self) -> AsyncIOMotorDatabase:
        if self._database is None:
            raise RuntimeError("Database not connected . call connect() first")
        return self._database

    async def connect(
        self,
        database_name: str = Settings.DATABASE_NAME,
        connection_string: str = Settings.MONGODB_URL,
        **kwargs,
    ):
        """connect to mongodb"""

        connection_options = {
            "connectTimeoutMS": 30000,
            "socketTimeoutMS": 30000,
            "maxPoolSize": 20,
            "minPoolSize": 5,
            "maxIdleTimeMS": 30000,
            "retryWrites": True,
            **kwargs,
        }
        try:

            logger.info("connecting to client")
            self._client: AsyncIOMotorClient = AsyncIOMotorClient(
                connection_string, **connection_options
            )
            logger.info("Connected to client")

            await self._client.admin.command("ping")
            self._database = self._client[database_name]
            logger.info(f"Successfully Connected to MongoDB database:{database_name}")

            server_info = await self._client.server_info()
            logger.info(f"MongoDB version: {server_info.get('version', 'Unknown')}")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to  connect to MongoDB: {e}")
            await self.disconnect()
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            await self.disconnect()
            raise

    async def get_collection(self, collection_name):
        if self._database is None:
            await self.connect()
        return self._database[collection_name]

    async def disconnect(self) -> None:
        if self._client:
            self._client.close() 
            self._database = None
            self._client = None
            logger.info("MongoDB connection closed")

    async def health_check(self) -> dict:
        """Check database health"""
        try:
            # Ping the database
            start_time = asyncio.get_event_loop().time()
            await self.client.admin.command("ping")
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000

            # Get database stats
            stats = await self.database.command("dbStats")

            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "database_size_mb": round(stats.get("dataSize", 0) / (1024 * 1024), 2),
                "collections": stats.get("collections", 0),
                "indexes": stats.get("indexes", 0),
                "connected": True,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "connected": False}


db_connection = DatabaseConnection()
