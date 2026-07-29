"""Validates generated/retrieved SQL before it is ever executed."""

import re
from typing import Any, Dict, Optional

import sqlparse

from app.config.log_config import logger
from app.constants.app_constants import ORDER_DB_TABLES, SQL_ASSISTANT
from app.exceptions import ValidationError
from app.repository.sql_repository.order_repository import order_repository

_ALLOWED_TABLES = {table.value for table in ORDER_DB_TABLES}


class SqlValidationService:
    """Validates SQL statements for safety, structure, and executability."""

    def validate(self, sql: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Run the full validation pipeline on a SQL statement.

        Args:
            sql: Candidate SQL statement.
            params: Optional bind parameters, used when running EXPLAIN.

        Returns:
            The (possibly trimmed) validated SQL string.

        Raises:
            ValidationError: If the statement fails any validation step.
        """
        sql = sql.strip().rstrip(";")

        self._validate_syntax(sql)
        self._validate_statement_type(sql)
        self._validate_forbidden_keywords(sql)
        self._validate_tables_exist(sql)
        self._validate_execution_plan(sql, params)

        return sql

    def _validate_syntax(self, sql: str) -> None:
        """Ensure the SQL parses into exactly one statement.

        Args:
            sql: SQL statement to check.

        Raises:
            ValidationError: If parsing fails or yields zero/multiple statements.
        """
        if not sql:
            raise ValidationError("Generated SQL is empty.")

        try:
            parsed = sqlparse.parse(sql)
        except Exception as exc:
            logger.exception("SQL syntax parse failed: %s", exc)
            raise ValidationError("Generated SQL could not be parsed.") from exc

        statements = [p for p in parsed if str(p).strip()]
        if len(statements) != 1:
            raise ValidationError(
                "Only a single SQL statement is allowed per query."
            )

    def _validate_statement_type(self, sql: str) -> None:
        """Ensure the statement is a read-only SELECT/CTE.

        Args:
            sql: SQL statement to check.

        Raises:
            ValidationError: If the statement is not a SELECT/WITH query.
        """
        first_word = sql.strip().split(None, 1)[0].lower() if sql.strip() else ""
        allowed = SQL_ASSISTANT.ALLOWED_STATEMENT_PREFIXES.value
        if first_word not in allowed:
            raise ValidationError(
                "Only read-only SELECT queries are permitted for this assistant."
            )

    def _validate_forbidden_keywords(self, sql: str) -> None:
        """Reject statements containing data/schema-modifying keywords.

        Args:
            sql: SQL statement to check.

        Raises:
            ValidationError: If a forbidden keyword is present as a standalone token.
        """
        lowered = sql.lower()
        for keyword in SQL_ASSISTANT.FORBIDDEN_KEYWORDS.value:
            if re.search(rf"\b{keyword}\b", lowered):
                raise ValidationError(
                    f"Query contains a disallowed operation: '{keyword}'."
                )

    def _validate_tables_exist(self, sql: str) -> None:
        """Ensure every referenced table is part of the known schema.

        Args:
            sql: SQL statement to check.

        Raises:
            ValidationError: If an unknown table is referenced.
        """
        referenced = set(
            match.lower()
            for match in re.findall(
                r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", sql, flags=re.IGNORECASE
            )
        )
        unknown = referenced - _ALLOWED_TABLES
        if unknown:
            raise ValidationError(
                f"Query references unknown table(s): {', '.join(sorted(unknown))}."
            )
        if not referenced:
            raise ValidationError("Query does not reference any known table.")

    def _validate_execution_plan(
        self, sql: str, params: Optional[Dict[str, Any]]
    ) -> None:
        """Run EXPLAIN to confirm the query is executable (catches bad joins/columns).

        Args:
            sql: SQL statement to check.
            params: Optional bind parameters required to run EXPLAIN.

        Raises:
            ValidationError: If EXPLAIN fails.
        """
        try:
            order_repository.explain(sql, params or {})
        except Exception as exc:
            logger.warning("Execution plan validation failed: %s", exc)
            raise ValidationError(
                "Query failed execution plan validation (check joins/columns)."
            ) from exc


sql_validation_service = SqlValidationService()
