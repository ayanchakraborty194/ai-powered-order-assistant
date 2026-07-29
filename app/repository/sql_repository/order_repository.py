"""Executes validated, read-only SQL against the Order Processing database."""

from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config.env_config import settings
from app.config.log_config import logger
from app.config.postgres_config import postgres_config
from app.exceptions import InternalError


class OrderRepository:
    """Data access layer for the order-processing business database."""

    def __init__(self) -> None:
        """Initialize with the shared Postgres config."""
        self.postgres_config = postgres_config

    def execute_select(
        self, sql: str, params: Dict[str, Any] | None = None
    ) -> List[Dict[str, Any]]:
        """Execute a validated read-only SQL statement with a hard row cap.

        Assumes the SQL has already passed validation (SELECT-only, no
        forbidden keywords) — this method focuses on safe execution, not
        validation.

        Args:
            sql: The SQL statement to execute (already validated).
            params: Optional named bind parameters.

        Returns:
            List of row dicts (column name -> value), capped at
            settings.SQL_QUERY_MAX_ROWS.

        Raises:
            InternalError: If the database query fails.
        """
        max_rows = settings.SQL_QUERY_MAX_ROWS
        statement_options = text(sql).execution_options(
            timeout=settings.SQL_QUERY_TIMEOUT_SECONDS
        )

        try:
            with self.postgres_config.get_session() as session:
                # Use Postgres statement_timeout so the DB itself enforces the cap,
                # in addition to any driver-level timeout options above.
                session.execute(
                    text(
                        f"SET statement_timeout = {settings.SQL_QUERY_TIMEOUT_SECONDS * 1000}"
                    )
                )
                result = session.execute(statement_options, params or {})
                columns = list(result.keys())
                rows = result.fetchmany(max_rows)
                return [dict(zip(columns, row)) for row in rows]
        except SQLAlchemyError as exc:
            logger.exception("SQL execution failed: %s", exc)
            raise InternalError("Query execution failed") from exc

    def explain(self, sql: str, params: Dict[str, Any] | None = None) -> str:
        """Run EXPLAIN on a statement to sanity-check its execution plan.

        Args:
            sql: SQL statement to explain.
            params: Optional named bind parameters.

        Returns:
            The execution plan as a single string.

        Raises:
            InternalError: If EXPLAIN fails (e.g. invalid SQL/table/columns).
        """
        try:
            with self.postgres_config.get_session() as session:
                result = session.execute(text(f"EXPLAIN {sql}"), params or {})
                plan_lines = [row[0] for row in result.fetchall()]
                return "\n".join(plan_lines)
        except SQLAlchemyError as exc:
            logger.exception("EXPLAIN failed: %s", exc)
            raise InternalError("Query plan validation failed") from exc


order_repository = OrderRepository()
