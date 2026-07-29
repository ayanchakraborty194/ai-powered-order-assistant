from app.services.core_services.nl_to_sql_service import NLToSQLService
from app.utils.core_utils.sql_cache_utils import normalize_query


def test_normalize_query_is_case_and_punctuation_insensitive():
    """Equivalent questions differing only in case/punctuation hash the same."""
    key_a = normalize_query("Show pending shipments!")
    key_b = normalize_query("show pending shipments")
    assert key_a == key_b


def test_normalize_query_differs_for_different_questions():
    """Distinct questions must hash to distinct keys."""
    key_a = normalize_query("Show pending shipments")
    key_b = normalize_query("Show delayed shipments")
    assert key_a != key_b


def test_strip_markdown_fences_removes_sql_fence():
    """LLM output wrapped in ```sql fences should be cleaned to raw SQL."""
    raw = "```sql\nSELECT * FROM orders\n```"
    cleaned = NLToSQLService._strip_markdown_fences(raw)
    assert cleaned == "SELECT * FROM orders"


def test_strip_markdown_fences_passthrough_when_no_fence():
    """Already-clean SQL should pass through unchanged."""
    raw = "SELECT * FROM orders"
    cleaned = NLToSQLService._strip_markdown_fences(raw)
    assert cleaned == "SELECT * FROM orders"
