"""Intent-detection step: identifies required tables, entities, and missing info."""

import json
import re
from typing import Any, Dict

from app.config.log_config import logger
from app.exceptions import InternalError
from app.llms.llm_factory import get_default_chat_client
from app.prompts.intent_prompt import INTENT_PROMPT
from app.utils.core_utils.llm_response_utils import extract_text_content

# class IntentAgent:
#     """Single-shot LLM call that extracts structured intent from a user query."""

#     def __init__(self) -> None:
#         """Initialize with the default chat client."""
#         self.llm = get_default_chat_client()

#     def detect(self, query: str) -> Dict[str, Any]:
#         """Extract tables, entities, and missing-info prompt from a query.

#         Args:
#             query: User's natural language question.

#         Returns:
#             Dict with keys "tables" (list[str]), "entities" (dict), and
#             "missing_info" (str or None).

#         Raises:
#             InternalError: If the LLM response cannot be parsed as JSON.
#         """
#         messages = [
#             ("system", INTENT_PROMPT),
#             ("user", query),
#         ]

#         try:
#             response = self.llm.invoke(messages)
#             raw = getattr(response, "content", str(response))
#         except Exception as exc:
#             logger.exception("Intent detection LLM call failed: %s", exc)
#             raise InternalError("Could not understand the question") from exc

#         parsed = self._parse_json(raw)
#         parsed.setdefault("tables", [])
#         parsed.setdefault("entities", {})
#         parsed.setdefault("missing_info", None)
#         return parsed

#     @staticmethod
#     def _parse_json(raw: str) -> Dict[str, Any]:
#         """Parse the LLM's JSON response, tolerating stray markdown fences.

#         Args:
#             raw: Raw LLM text output.

#         Returns:
#             Parsed dict.

#         Raises:
#             InternalError: If parsing fails entirely.
#         """
#         cleaned = raw.strip()
#         cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
#         cleaned = re.sub(r"\s*```$", "", cleaned)

#         try:
#             return json.loads(cleaned)
#         except json.JSONDecodeError as exc:
#             logger.exception("Failed to parse intent JSON: %s | raw=%s", exc, raw)
#             raise InternalError("Could not understand the question") from exc

class IntentAgent:
    """Single-shot LLM call that extracts structured intent from a user query."""

    def __init__(self) -> None:
        """Initialize with the default chat client."""
        self.llm = get_default_chat_client()

    def detect(self, query: str) -> Dict[str, Any]:
        """Extract tables, entities, and missing-info prompt from a query.

        Args:
            query: User's natural language question.

        Returns:
            Dict with keys "tables" (list[str]), "entities" (dict), and
            "missing_info" (str or None).

        Raises:
            InternalError: If the LLM response cannot be parsed as JSON.
        """
        messages = [
            ("system", INTENT_PROMPT),
            ("user", query),
        ]

        try:
            response = self.llm.invoke(messages)
            raw = extract_text_content(response)
            
            # Normalize list content to a plain string if returned as content blocks
            if isinstance(raw, list):
                raw_text = "".join(
                    part if isinstance(part, str) else part.get("text", "")
                    for part in raw
                )
            else:
                raw_text = str(raw)

        except Exception as exc:
            logger.exception("Intent detection LLM call failed: %s", exc)
            raise InternalError("Could not understand the question") from exc

        parsed = self._parse_json(raw_text)
        parsed.setdefault("tables", [])
        parsed.setdefault("entities", {})
        parsed.setdefault("missing_info", None)
        return parsed

    @staticmethod
    def _parse_json(raw: Any) -> Dict[str, Any]:
        """Parse the LLM's JSON response, tolerating stray markdown fences.

        Args:
            raw: Raw LLM text output (or content structure).

        Returns:
            Parsed dict.

        Raises:
            InternalError: If parsing fails entirely.
        """
        if not isinstance(raw, str):
            if isinstance(raw, list):
                raw = "".join(
                    item if isinstance(item, str) else str(item) 
                    for item in raw
                )
            else:
                raw = str(raw)

        cleaned = raw.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.exception("Failed to parse intent JSON: %s | raw=%s", exc, raw)
            raise InternalError("Could not understand the question") from exc
        
intent_agent = IntentAgent()
