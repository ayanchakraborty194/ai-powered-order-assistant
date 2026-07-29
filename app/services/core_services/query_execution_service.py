"""Executes validated SQL safely, enforcing the configured execution timeout."""

import concurrent.futures
from typing import Any, Dict, List, Optional

from app.config.env_config import settings
from app.config.log_config import logger
from app.exceptions import InternalError, ValidationError
from app.repository.sql_repository.order_repository import order_repository


class QueryExecutionService:
    """Executes SQL against the order-processing DB with a wall-clock timeout."""

    def __init__(self) -> None:
        """Initialize with a small thread pool for timeout enforcement."""
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def execute(
        self, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a validated SQL statement within the configured timeout.

        Args:
            sql: Validated, read-only SQL statement.
            params: Optional bind parameters.

        Returns:
            List of row dicts.

        Raises:
            ValidationError: If the query exceeds the execution timeout.
            InternalError: If execution otherwise fails.
        """
        timeout = settings.SQL_QUERY_TIMEOUT_SECONDS
        future = self._executor.submit(
            order_repository.execute_select, sql, params or {}
        )

        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError as exc:
            future.cancel()
            logger.warning("Query execution exceeded %ss timeout.", timeout)
            raise ValidationError(
                f"Query took longer than {timeout} seconds and was aborted."
            ) from exc
        except (ValidationError, InternalError):
            raise
        except Exception as exc:
            logger.exception("Unexpected error during query execution: %s", exc)
            raise InternalError("Query execution failed unexpectedly") from exc


query_execution_service = QueryExecutionService()
