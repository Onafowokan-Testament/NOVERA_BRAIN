"""Application configuration settings.

Consolidates all application-wide configuration in one place.
Environment variables should be defined in .env file.
"""

import os
from pathlib import Path
from typing import Optional

from decouple import config as get_env


class Settings:
    """Main application settings."""

    # ==================== Application ====================
    LOG_LEVEL: str = "DEBUG"
    LOG_DIR: Path = Path(__file__).parent.parent.parent / "logs"
    APP_NAME: str = "NOVERA_AGENT"
    APP_VERSION: str = "0.0.1"

    # ==================== Bot & Telegram ====================
    BOT_TOKEN: str = get_env("BOT_TOKEN")
    TEST_BOT_TOKEN: str = get_env("TEST_BOT_TOKEN")

    # ==================== Database ====================
    # MongoDB
    MONGODB_URL: str = get_env("MONGODB_URL")
    MONGODB_PASSWORD: str = get_env("MONGODB_PASSWORD")
    MONGO_USERNAME: str = get_env("MONGO_USERNAME")
    DATABASE_NAME: str = "novera"
    DATABASE_URL: str = get_env("DATABASE_URL")

    # PostgreSQL
    POSTGRES_URL: str = get_env("POSTGRES_URL")

    # Cache
    REDIS_URL: str = get_env("REDIS_URL")

    # ==================== LLM & AI Services ====================
    OPENAI_API_KEY: str = get_env("OPENAI_API_KEY")
    MODEL_NAME: str = get_env("MODEL_NAME", default="gpt-4o-mini")
    EMBEDDING_MODEL_NAME: str = get_env(
        "EMBEDDING_MODEL_NAME", default="text-embedding-3-small"
    )

    # ==================== External APIs ====================
    TAVILY_API_KEY: str = get_env("TAVILY_API_KEY")
    QDRANT_API_KEY: str = get_env("QDRANT_API_KEY")
    QDRANT_API_ENDPOINT: str = get_env("QDRANT_ENDPOINT")

    # OpenRouteService (for directions)
    ORS_API_KEY: str = get_env("ORS_API_KEY")
    ORS_BASE_URL: str = "https://api.openrouteservice.org/v2/directions/foot-walking"
    CACHE_TIMEOUT: int = 3600

    # ==================== LangSmith (Tracing) ====================
    LANGSMITH_TRACING: bool = get_env("LANGSMITH_TRACING", default=True, cast=bool)
    LANGSMITH_ENDPOINT: str = get_env(
        "LANGSMITH_ENDPOINT", default="https://api.smith.langchain.com"
    )
    LANGSMITH_API_KEY: str = get_env("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT: str = get_env("LANGSMITH_PROJECT", default="NOVERA")

    # ==================== Bot Configuration ====================
    ADMIN_IDS: list[int] = [1482138353]  # Admin user IDs for special commands

    def __init__(self) -> None:
        """Initialize settings and configure environment variables."""
        self._configure_langsmith()
        self._configure_openai()

    def _configure_langsmith(self) -> None:
        """Configure LangSmith environment variables."""
        if self.LANGSMITH_TRACING:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_ENDPOINT"] = self.LANGSMITH_ENDPOINT
            os.environ["LANGCHAIN_API_KEY"] = self.LANGSMITH_API_KEY
            os.environ["LANGCHAIN_PROJECT"] = self.LANGSMITH_PROJECT

    def _configure_openai(self) -> None:
        """Configure OpenAI environment variables."""
        if self.OPENAI_API_KEY:
            os.environ["OPENAI_API_KEY"] = self.OPENAI_API_KEY

    @classmethod
    def validate_keys(cls) -> None:
        """Validate that all required environment variables are set.

        Raises:
            ValueError: If any required environment variables are missing.
        """
        required_vars = [
            "BOT_TOKEN",
            "DATABASE_URL",
            "POSTGRES_URL",
            "OPENAI_API_KEY",
            "QDRANT_ENDPOINT",
            "QDRANT_API_KEY",
        ]
        missing_secrets = [
            var for var in required_vars if not get_env(var, default=None)
        ]

        if missing_secrets:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_secrets)}"
            )


# Global settings instance
settings = Settings()
