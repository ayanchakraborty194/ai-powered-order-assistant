"""Formats raw SQL result rows into a business-friendly natural language answer."""

import json
from typing import Any, Dict, List

from app.config.log_config import logger
from app.llms.llm_factory import get_default_chat_client
from app.prompts.response_formatting_prompt import RESPONSE_FORMATTING_PROMPT
from app.utils.core_utils.llm_response_utils import extract_text_content

class ResponderAgent:
    """Single-shot LLM call that turns rows into a natural language answer."""

    def __init__(self) -> None:
        """Initialize with the default chat client."""
        self.llm = get_default_chat_client()

    def format_response(self, query: str, rows: List[Dict[str, Any]]) -> str:
        """Generate a business-friendly answer from raw query result rows.

        Args:
            query: The user's original natural language question.
            rows: Raw result rows returned by the executed SQL query.

        Returns:
            A concise natural-language response. Falls back to a plain
            summary if the LLM call fails.
        """
        if not rows:
            return "I couldn't find any matching records for that question."

        prompt = RESPONSE_FORMATTING_PROMPT.format(
            query=query, rows=json.dumps(rows, default=str)
        )

        try:
            response = self.llm.invoke(prompt)
            return extract_text_content(response).strip()        
        except Exception as exc:
            logger.exception("Response formatting failed, using fallback: %s", exc)
            return self._fallback_summary(rows)

    @staticmethod
    def _fallback_summary(rows: List[Dict[str, Any]]) -> str:
        """Produce a minimal summary if the LLM formatting call fails.

        Args:
            rows: Raw result rows.

        Returns:
            A basic sentence describing the row count.
        """
        return f"Found {len(rows)} matching record(s)."


responder_agent = ResponderAgent()
