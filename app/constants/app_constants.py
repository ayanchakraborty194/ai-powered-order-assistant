"""Application constants: model config, vector DB settings, route paths, domain rules."""

from enum import Enum


class GEMINI_CHAT_MODEL(Enum):
    """Gemini chat model configuration."""

    MODEL_NAME = "gemini-3.5-flash-lite"
    TEMPERATURE = 0.0


class VECTOR_DB(Enum):
    """Vector database configuration constants (schema metadata RAG)."""

    EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"


class ROUTE_CONSTANTS(Enum):
    """API route/path constants shared across the app."""

    API_V1_PREFIX = "/api/v1"


class ORDER_DB_TABLES(Enum):
    """Table names in the Order Processing (PostgreSQL) database."""

    CUSTOMERS = "customers"
    ORDERS = "orders"
    ORDER_ITEMS = "order_items"
    PRODUCTS = "products"
    SHIPMENTS = "shipments"


class SQL_ASSISTANT(Enum):
    """Behavioral constants for the NL-to-SQL assistant."""

    # Only read-only statements are ever allowed to execute.
    ALLOWED_STATEMENT_PREFIXES = ("select", "with")
    FORBIDDEN_KEYWORDS = (
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "grant",
        "revoke",
        "create",
        "call",
        "merge",
        "copy",
        "vacuum",
    )
    CACHE_KEY_PREFIX = "sql_cache:"
    CACHE_SIMILARITY_THRESHOLD = 0.92
