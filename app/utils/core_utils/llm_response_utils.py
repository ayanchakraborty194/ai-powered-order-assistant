"""Helpers for safely extracting plain text from LLM chat responses.

Newer langchain-google-genai / Gemini responses can return `.content` as a
plain string, OR as a "content block" (a dict like {"type": "text", "text":
"...", "extras": {...}}), OR as a list of such blocks. This normalizes all
three shapes into a single plain string.
"""

from typing import Any


def extract_text_content(response: Any) -> str:
    """Extract plain text from an LLM chat response, regardless of content shape.

    Args:
        response: The object returned by `llm.invoke(...)` (e.g. an AIMessage).

    Returns:
        The concatenated plain text content.
    """
    content = getattr(response, "content", None)

    if content is None:
        return str(response)

    if isinstance(content, str):
        return content

    if isinstance(content, dict):
        return content.get("text", "") if content.get("type") == "text" else str(content)

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "".join(parts)

    return str(content)