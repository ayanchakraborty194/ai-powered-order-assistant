"""Repository layer for data access.

This module provides organized access to:
- SQL: order-processing database repositories and the SQL retrieval strategy
- Vector: Qdrant vector repository for schema-metadata embeddings
"""

from app.repository.sql_repository import (
    order_repository,
    query_cache_repository,
    sql_template_repository,
)
from app.repository.vector_repository import qdrant_repository

__all__ = [
    "order_repository",
    "query_cache_repository",
    "sql_template_repository",
    "qdrant_repository",
]
