import pytest

from app.exceptions import ValidationError
from app.services.core_services.sql_validation_service import SqlValidationService


@pytest.fixture
def validation_service(monkeypatch):
    """Provide a validation service with EXPLAIN mocked out (no real DB needed)."""
    service = SqlValidationService()
    monkeypatch.setattr(
        "app.services.core_services.sql_validation_service.order_repository.explain",
        lambda sql, params=None: "Seq Scan on orders",
    )
    return service


def test_valid_select_passes(validation_service):
    """A well-formed SELECT against known tables should validate cleanly."""
    sql = "SELECT order_id FROM orders WHERE status = :status"
    result = validation_service.validate(sql, {"status": "Pending"})
    assert "SELECT" in result.upper()


def test_rejects_non_select_statement(validation_service):
    """Non-SELECT statements must be rejected outright."""
    with pytest.raises(ValidationError):
        validation_service.validate("DELETE FROM orders WHERE order_id = 1")


def test_rejects_forbidden_keyword_inside_select(validation_service):
    """A forbidden keyword anywhere in the statement should be rejected."""
    with pytest.raises(ValidationError):
        validation_service.validate(
            "SELECT * FROM orders; DROP TABLE orders;"
        )


def test_rejects_unknown_table(validation_service):
    """Referencing a table outside the known schema must be rejected."""
    with pytest.raises(ValidationError):
        validation_service.validate("SELECT * FROM secret_admin_table")


def test_rejects_multiple_statements(validation_service):
    """Only a single statement may be submitted per query."""
    with pytest.raises(ValidationError):
        validation_service.validate(
            "SELECT * FROM orders; SELECT * FROM customers;"
        )
