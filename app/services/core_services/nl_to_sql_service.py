"""Implements the 3-layer SQL retrieval strategy:

Layer 1: previously executed SQL cache (Redis)
Layer 2: predefined SQL template repository
Layer 3: dynamic SQL generation via LLM + schema RAG context
"""

import json
import re
from typing import Any, Dict, Optional

from app.config.log_config import logger
from app.exceptions import InternalError
from app.llms.llm_factory import get_default_chat_client
from app.prompts.sql_generation_prompt import SQL_GENERATION_PROMPT
from app.repository.sql_repository.query_cache_repository import (
    query_cache_repository,
)
from app.repository.sql_repository.sql_template_repository import (
    sql_template_repository,
)
from app.services.core_services.schema_metadata_service import (
    schema_metadata_service,
)
from app.services.core_services.schema_metadata_service import (
    get_schema_documents,
    schema_metadata_service,
)
from app.utils.core_utils.llm_response_utils import extract_text_content

# Entity keys whose values should be wrapped as ILIKE wildcards when bound.
_WILDCARD_PARAMS = {"customer_name", "product_name", "delivery_status"}


class NLToSQLResult:
    """Result of resolving a NL query into an executable SQL statement."""

    def __init__(self, sql: str, params: Dict[str, Any], source: str) -> None:
        """Initialize the result.

        Args:
            sql: The resolved SQL statement (with named bind placeholders).
            params: Bind parameters to execute the statement with.
            source: One of "cache", "template", "llm_generated".
        """
        self.sql = sql
        self.params = params
        self.source = source


class NLToSQLService:
    """Resolves a natural language query into SQL using the layered strategy."""

    def resolve(self, query: str, entities: Dict[str, Any]) -> NLToSQLResult:
        """Resolve a query to SQL, trying cache, then templates, then the LLM.

        Args:
            query: User's natural language question.
            entities: Entities extracted by the intent-detection step.

        Returns:
            NLToSQLResult describing the resolved SQL, params, and source layer.
        """
        cached = self._try_cache(query)
        if cached is not None:
            return cached

        templated = self._try_template(query, entities)
        if templated is not None:
            return templated

        return self._generate_with_llm(query, entities)

    def remember(self, query: str, result: NLToSQLResult) -> None:
        """Persist a successfully executed SQL result into the cache.

        Args:
            query: The original user query.
            result: The NLToSQLResult that was successfully validated/executed.
        """
        query_cache_repository.set(query, result.sql, result.params)

    def _try_cache(self, query: str) -> Optional[NLToSQLResult]:
        """Attempt Layer 1: exact cache lookup.

        Args:
            query: User's natural language question.

        Returns:
            NLToSQLResult on a cache hit, else None.
        """
        cached = query_cache_repository.get(query)
        if cached is None:
            return None
        logger.info("SQL cache hit for query.")
        return NLToSQLResult(sql=cached["sql"], params=cached.get("params", {}), source="cache")

    def _try_template(
        self, query: str, entities: Dict[str, Any]
    ) -> Optional[NLToSQLResult]:
        """Attempt Layer 2: predefined SQL template match.

        Args:
            query: User's natural language question.
            entities: Extracted entities to fill template bind parameters.

        Returns:
            NLToSQLResult if a template matched and all its required
            parameters could be filled, else None.
        """
        template = sql_template_repository.find_best_match(query)
        if template is None:
            return None

        required_params = set(re.findall(r":(\w+)", template.sql))
        params: Dict[str, Any] = {}

        for param_name in required_params:
            value = entities.get(param_name)
            if value in (None, ""):
                logger.info(
                    "Template '%s' matched but missing param '%s'; falling back.",
                    template.name,
                    param_name,
                )
                return None
            if param_name in _WILDCARD_PARAMS:
                value = f"%{value}%"
            params[param_name] = value

        logger.info("SQL template match: %s", template.name)
        return NLToSQLResult(sql=template.sql, params=params, source="template")

    def _generate_with_llm(
        self, query: str, entities: Dict[str, Any]
    ) -> NLToSQLResult:
        """Attempt Layer 3: dynamic SQL generation via LLM + schema RAG.

        Args:
            query: User's natural language question.
            entities: Extracted entities, passed to the LLM as generation hints.

        Returns:
            NLToSQLResult with source="llm_generated".

        Raises:
            InternalError: If the LLM fails to produce usable SQL.
        """
        schema_docs = schema_metadata_service.retrieve_relevant_schema(query)
        schema_context = "\n".join(doc.page_content for doc in schema_docs)

        if not schema_context.strip():
            logger.warning(
                "Schema context was empty for query=%r; using full schema catalog.",
                query,
            )
            schema_context = "\n".join(
                doc.page_content for doc in get_schema_documents()
            )

        prompt = SQL_GENERATION_PROMPT.format(
            schema_context=schema_context,
            query=query,
            entities=json.dumps(entities, default=str),
        )

        llm = get_default_chat_client()
        try:
            response = llm.invoke(prompt)
            raw_sql = extract_text_content(response)        
        except Exception as exc:
            logger.exception("LLM SQL generation failed: %s", exc)
            raise InternalError("Could not generate SQL for this question") from exc

        sql = self._strip_markdown_fences(raw_sql)

        bind_names = set(re.findall(r":(\w+)", sql))
        params: Dict[str, Any] = {}
        for name in bind_names:
            value = entities.get(name)
            if value is not None:
                if name in _WILDCARD_PARAMS:
                    value = f"%{value}%"
                params[name] = value

        logger.info("SQL generated dynamically via LLM.")
        return NLToSQLResult(sql=sql, params=params, source="llm_generated")

    @staticmethod
    def _strip_markdown_fences(text: str) -> str:
        """Remove ```sql fences the LLM may still wrap around its output.

        Args:
            text: Raw LLM output.

        Returns:
            Cleaned SQL string.
        """
        # cleaned = text.strip()
        # cleaned = re.sub(r"^```(?:sql)?\s*", "", cleaned)
        # cleaned = re.sub(r"\s*```$", "", cleaned)
        # return cleaned.strip()
        # 1. Ensure 'text' is extracted as a string if it's passed as a list/part
        if isinstance(text, list):
            # Join string elements or extract .text attribute if objects are present
            text = "".join(
                item.text if hasattr(item, "text") else str(item) for item in text
            )
        elif not isinstance(text, str):
            text = str(text)

        # 2. Perform the cleaning/stripping safely
        cleaned = text.strip()

        if cleaned.startswith("```"):
            # Remove opening fence (e.g. ```sql)
            cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            # Remove closing fence
            cleaned = cleaned.rsplit("\n", 1)[0]
        return cleaned.strip()


nl_to_sql_service = NLToSQLService()
