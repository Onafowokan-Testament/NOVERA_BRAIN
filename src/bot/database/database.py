import asyncio
import threading
from typing import Optional

from settings.logger_config import logger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from settings.config import Settings

Settings.validate_keys()


class DatabaseConnection:
    """Singleton MongoDB connection manager"""

    _instance = None
    _lock = threading.Lock()  # Thread safety for singleton
    _client: Optional[AsyncIOMotorClient] = None
    _database: Optional[AsyncIOMotorDatabase] = None
    _connected: bool = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    async def get_client(self) -> AsyncIOMotorClient:
        """Get the MongoDB client, connecting if necessary"""
        if not self._connected or self._client is None:
            logger.info("Connecting to database first")
            await self.connect()
        return self._client

    @property
    def database(self) -> AsyncIOMotorDatabase:
        """Get the database instance"""
        if self._database is None:
            raise RuntimeError("Database not connected. Call connect() first")
        return self._database

    @property
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._connected and self._client is not None

    async def connect(
        self,
        database_name: str = Settings.DATABASE_NAME,
        connection_string: str = Settings.MONGODB_URL,
        **kwargs,
    ):
        """Connect to MongoDB"""

        if self._connected and self._client is not None:
            logger.info("Already connected to database")
            return

        connection_options = {
            "connectTimeoutMS": 300000,
            "socketTimeoutMS": 300000,
            "maxPoolSize": 20,
            "minPoolSize": 5,
            "maxIdleTimeMS": 300000,
            "retryWrites": True,
            "retryReads": True,
            **kwargs,
        }

        try:
            logger.info("Connecting to MongoDB client")
            self._client = AsyncIOMotorClient(connection_string, **connection_options)
            logger.info("Connected to client")

            # Test the connection
            await self._client.admin.command("ping")
            logger.info("Ping successful")

            self._database = self._client[database_name]
            self._connected = True
            logger.info(f"Successfully connected to MongoDB database: {database_name}")

            server_info = await self._client.server_info()
            logger.info(f"MongoDB version: {server_info.get('version', 'Unknown')}")

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            await self.disconnect()
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            await self.disconnect()
            raise

    async def get_collection(self, collection_name: str):
        """Get a collection, connecting if necessary"""
        if not self.is_connected:
            await self.connect()
        return self._database[collection_name]

    async def disconnect(self) -> None:
        """Disconnect from MongoDB"""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            self._connected = False
            logger.info("MongoDB connection closed")

    async def health_check(self) -> dict:
        """Check database health"""
        try:
            if not self.is_connected:
                return {
                    "status": "unhealthy",
                    "error": "Not connected",
                    "connected": False,
                }

            start_time = asyncio.get_event_loop().time()
            await self._client.admin.command("ping")
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000

            # Get database stats
            stats = await self._database.command("dbStats")

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

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()


# Global instance
db_connection = DatabaseConnection()
