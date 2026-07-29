"""Main orchestrator for the Order Processing NL-to-SQL assistant.

Flow: intent detection -> (ask for missing info | resolve SQL via cache/
template/LLM) -> validate -> execute -> cache -> format response.
"""

from typing import Any, Dict, Optional

from app.agents.intent_agent import intent_agent
from app.agents.responder_agent import responder_agent
from app.config.log_config import logger
from app.config.redis_config import redis_config
from app.exceptions import InternalError, ValidationError
from app.services.core_services.nl_to_sql_service import nl_to_sql_service
from app.services.core_services.query_execution_service import (
    query_execution_service,
)
from app.services.core_services.sql_validation_service import sql_validation_service
from app.repository.sql_repository.chat_history_repository import (
    chat_history_repository,
)
_PENDING_KEY_PREFIX = "sql_pending_clarification:"
_PENDING_TTL_SECONDS = 600


class SqlAgent:
    """Orchestrates the end-to-end NL-to-SQL-to-answer pipeline."""

    def __init__(self) -> None:
        """Initialize with a Redis client for multi-turn clarification state."""
        self.redis_client = redis_config.get_redis_client()

    def invoke(self, thread_id: str, query: str) -> Dict[str, Any]:
        """Run the full pipeline for a single user turn.

        Args:
            thread_id: Conversation thread identifier (used for multi-turn
                clarification memory).
            query: The user's natural language question.

        Returns:
            Dict with keys: "answer" (str), "needs_clarification" (bool),
            "sql" (str or None), "source" (str or None).
        """
        chat_history_repository.add_message(thread_id, role="user", content=query)
        effective_query = self._merge_with_pending(thread_id, query)

        intent = intent_agent.detect(effective_query)

        if intent.get("missing_info"):
            self._store_pending(thread_id, effective_query)
            answer = intent["missing_info"]
            chat_history_repository.add_message(thread_id, role="assistant", content=answer)
            return {
                "answer": answer,
                "needs_clarification": True,
                "sql": None,
                "source": None,
            }

        self._clear_pending(thread_id)
        entities = intent.get("entities", {})

        try:
            result = nl_to_sql_service.resolve(effective_query, entities)
            logger.debug("Resolved SQL before validation: sql=%s params=%s", result.sql, result.params)
            validated_sql = sql_validation_service.validate(result.sql, result.params)
            rows = query_execution_service.execute(validated_sql, result.params)
            nl_to_sql_service.remember(effective_query, result)
        except (ValidationError, InternalError) as exc:
            logger.warning("SQL pipeline failed for query=%s: %s", effective_query, exc)
            answer =  (
                "I ran into a problem answering that question. Could you "
                "rephrase it or provide more detail (e.g. an Order ID or "
                "Customer Name)?"
            )
            chat_history_repository.add_message(thread_id, role="assistant", content=answer)
            return {
                "answer": answer,
                "needs_clarification": True,
                "sql": None,
                "source": None,
            }

        answer = responder_agent.format_response(effective_query, rows)
        chat_history_repository.add_message(
            thread_id, role="assistant", content=answer, sql=result.sql, source=result.source
        )

        return {
            "answer": answer,
            "needs_clarification": False,
            "sql": result.sql,
            "source": result.source,
        }

    def _pending_key(self, thread_id: str) -> str:
        """Build the Redis key for a thread's pending clarification state.

        Args:
            thread_id: Conversation thread identifier.

        Returns:
            Redis key string.
        """
        return f"{_PENDING_KEY_PREFIX}{thread_id}"

    def _store_pending(self, thread_id: str, query: str) -> None:
        """Remember the original query while awaiting the user's clarification.

        Args:
            thread_id: Conversation thread identifier.
            query: The original (unanswerable) query.
        """
        try:
            self.redis_client.set(
                self._pending_key(thread_id), query, ex=_PENDING_TTL_SECONDS
            )
        except Exception as exc:
            logger.warning("Failed to store pending clarification state: %s", exc)

    def _clear_pending(self, thread_id: str) -> None:
        """Clear any pending clarification state for a thread.

        Args:
            thread_id: Conversation thread identifier.
        """
        try:
            self.redis_client.delete(self._pending_key(thread_id))
        except Exception as exc:
            logger.warning("Failed to clear pending clarification state: %s", exc)

    def _merge_with_pending(self, thread_id: str, query: str) -> str:
        """Merge the current message with a prior unanswered question, if any.

        Args:
            thread_id: Conversation thread identifier.
            query: The current user message.

        Returns:
            The combined query if a pending clarification existed, else the
            original query unchanged.
        """
        try:
            pending: Optional[bytes] = self.redis_client.get(
                self._pending_key(thread_id)
            )
        except Exception as exc:
            logger.warning("Failed to read pending clarification state: %s", exc)
            return query

        if not pending:
            return query

        pending_str = pending if isinstance(pending, str) else pending.decode("utf-8")
        return f"{pending_str} ({query})"


sql_agent = SqlAgent()
