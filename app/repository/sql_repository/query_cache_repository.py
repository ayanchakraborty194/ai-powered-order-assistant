"""Redis-backed cache of previously executed natural-language-query -> SQL pairs.

This is Layer 1 of the SQL retrieval strategy: exact/near-duplicate questions
reuse a previously validated SQL statement instead of round-tripping to the LLM.
"""

import json
from typing import Optional

from app.config.env_config import settings
from app.config.log_config import logger
from app.config.redis_config import redis_config
from app.constants.app_constants import SQL_ASSISTANT
from app.utils.core_utils.sql_cache_utils import normalize_query


class QueryCacheRepository:
    """Cache of normalized NL query -> {sql, params} pairs, stored in Redis."""

    def __init__(self) -> None:
        """Initialize with the Redis client and configured TTL."""
        self.redis_client = redis_config.get_redis_client()
        self.ttl_seconds = settings.SQL_CACHE_TTL_SECONDS
        self.key_prefix = SQL_ASSISTANT.CACHE_KEY_PREFIX.value

    def _cache_key(self, query: str) -> str:
        """Build the Redis key for a normalized query.

        Args:
            query: Raw user query.

        Returns:
            Redis key string.
        """
        return f"{self.key_prefix}{normalize_query(query)}"

    def get(self, query: str) -> Optional[dict]:
        """Look up a cached SQL entry for a query.

        Args:
            query: Raw user query.

        Returns:
            Dict with keys "sql" and "params", or None on a cache miss.
        """
        try:
            raw = self.redis_client.get(self._cache_key(query))
            if raw is None:
                return None
            return json.loads(raw)
        except Exception as exc:
            logger.warning("Query cache read failed (treating as miss): %s", exc)
            return None

    def set(self, query: str, sql: str, params: Optional[dict] = None) -> None:
        """Store a validated SQL statement for a query.

        Args:
            query: Raw user query used as the cache key basis.
            sql: The SQL statement that successfully answered the query.
            params: Optional bound parameters used with the SQL statement.
        """
        try:
            payload = json.dumps({"sql": sql, "params": params or {}})
            self.redis_client.set(
                self._cache_key(query), payload, ex=self.ttl_seconds
            )
        except Exception as exc:
            logger.warning("Query cache write failed (non-fatal): %s", exc)


query_cache_repository = QueryCacheRepository()
