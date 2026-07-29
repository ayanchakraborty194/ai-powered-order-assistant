import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Load and expose environment settings for the application."""

    def __init__(self) -> None:
        """Initialize settings from environment variables."""
        # 1. Project information
        self.ENV: str = os.getenv("ENV", "dev")
        self.PROJECT_NAME: str = os.getenv("PROJECT_NAME", "ai_powered_order_assistant")
        self.PROJECT_VERSION: str = os.getenv("PROJECT_VERSION", "0.1.0")
        self.PROJECT_DESCRIPTION: str = os.getenv(
            "PROJECT_DESCRIPTION",
            "An AI-powered conversational assistant for order processing data (NL-to-SQL).",
        )

        # 2. API configuration
        self.ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "").split(",")
        self.BASE_PATH: str = os.getenv("BASE_PATH", "")

        # 3. LLM configuration (Gemini only — the only provider in scope)
        self.GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY", None)

        # 4. Working directory (logs, Hugging Face cache)
        working_dir = os.path.abspath(os.getenv("WORKING_DIR", ".").strip() or ".")
        self.WORKING_PROJECT_DIR: str = os.path.join(working_dir, self.PROJECT_NAME)
        self.LOG_DIR: str = os.path.join(self.WORKING_PROJECT_DIR, "logs")

        # 5. Hugging Face configuration (embedding model cache, for schema RAG)
        self.HF_HOME: str = os.getenv(
            "HF_HOME", os.path.join(self.WORKING_PROJECT_DIR, "hf")
        )
        os.environ.setdefault("HF_HOME", self.HF_HOME)

        # 6. Qdrant configuration (schema metadata RAG)
        self.COLLECTION_NAME: str = os.getenv(
            "COLLECTION_NAME", "ai_powered_order_assistant"
        )
        self.USE_ORDER_DB: bool = (
            os.getenv("USE_ORDER_DB", "true").strip().lower() == "true"
        )
        self.USE_QDRANT: bool = (
            os.getenv("USE_QDRANT", "true").strip().lower() == "true"
        )
        self.QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
        self.QDRANT_PORT = os.getenv("QDRANT_PORT", "6333")
        self.QDRANT_PROTOCOL = os.getenv("QDRANT_PROTOCOL", "http")

        # 7. Redis configuration (SQL cache + multi-turn clarification memory)
        self.REDIS_HOST = os.getenv("REDIS_HOST", "redis")
        self.REDIS_PORT = os.getenv("REDIS_PORT", "6379")
        self.REDIS_PROTOCOL = os.getenv("REDIS_PROTOCOL", "http")
        self.REDIS_DB = os.getenv("REDIS_DB", "0")

        # 8. Order Processing (PostgreSQL) configuration
        self.POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
        self.POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
        self.POSTGRES_DB: str = os.getenv("POSTGRES_DB", "order_processing")
        self.POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
        self.POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")

        # 9. NL-to-SQL assistant behavior
        self.SQL_QUERY_TIMEOUT_SECONDS: int = int(
            os.getenv("SQL_QUERY_TIMEOUT_SECONDS", "30")
        )
        self.SQL_QUERY_MAX_ROWS: int = int(os.getenv("SQL_QUERY_MAX_ROWS", "200"))
        self.SQL_CACHE_TTL_SECONDS: int = int(
            os.getenv("SQL_CACHE_TTL_SECONDS", "86400")
        )
        self.ORDER_SCHEMA_COLLECTION_NAME: str = os.getenv(
            "ORDER_SCHEMA_COLLECTION_NAME", "order_schema_metadata"
        )


settings = Settings()
