"""Helpers for turning natural-language queries into stable cache keys."""

import hashlib
import re


def normalize_query(query: str) -> str:
    """Normalize a query for cache-key hashing.

    Lowercases, strips punctuation/extra whitespace, then hashes so keys have
    a bounded, predictable length regardless of input length.

    Args:
        query: Raw user query.

    Returns:
        Hex digest string suitable for use as (part of) a Redis key.
    """
    normalized = query.strip().lower()
    normalized = re.sub(r"[^\w\s]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
