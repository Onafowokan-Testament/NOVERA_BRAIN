import os

from decouple import config


class Settings:
    BOT_TOKEN = config("BOT_TOKEN")
    TEST_BOT_TOKEN = config("TEST_BOT_TOKEN")

    DATABASE_URL = config("DATABASE_URL")

    POSTGRES_URL = config("POSTGRES_URL")
    REDIS_URL = config("REDIS_URL")
    TAVILY_API_KEY = config("TAVILY_API_KEY")
    QDRANT_API_KEY = config("QDRANT_API_KEY")
    QDRANT_API_ENDPOINT = config("QDRANT_ENDPOINT")

    LANGSMITH_TRACING = config("LANGSMITH_TRACING", default=True, cast=bool)
    LANGSMITH_ENDPOINT = config(
        "LANGSMITH_ENDPOINT", default="https://api.smith.langchain.com"
    )
    LANGSMITH_API_KEY = config("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT = config("LANGSMITH_PROJECT", "NOVERA")

    MODEL_NAME = config("MODEL_NAME", default="gpt-4o-mini")
    EMBEDDING_MODEL_NAME = config(
        "EMBEDDING_MODEL_NAME", default="text-embedding-3-small"
    )

    ORS_API_KEY = config("ORS_API_KEY")
    ORS_BASE_URL: str = "https://api.openrouteservice.org/v2/directions/foot-walking"
    CACHE_TIMEOUT: int = 3600

    OPENAI_API_KEY = config("OPENAI_API_KEY")

    # MONGODB
    MONGODB_PASSWORD = config("MONGODB_PASSWORD")
    MONGO_USERNAME = config("MONGO_USERNAME")
    MONGODB_URL = config("MONGODB_URL")
    DATABASE_NAME = "novera"

    if LANGSMITH_TRACING:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT
        os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    if OPENAI_API_KEY:
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

    @classmethod
    def validate_keys(cls):
        required_vars = [
            "BOT_TOKEN",
            "DATABASE_URL",
            "POSTGRES_URL",
            "OPENAI_API_KEY",
            "QDRANT_ENDPOINT",
            "QDRANT_API_KEY",
        ]
        missing_secret = [var for var in required_vars if not config(var, default=None)]

        if missing_secret:
            raise ValueError(f"Missing required env vars {', '.join(missing_secret)}")
