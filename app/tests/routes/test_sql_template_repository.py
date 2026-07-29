from app.repository.sql_repository.sql_template_repository import (
    SqlTemplateRepository,
)


def test_matches_orders_by_customer():
    """Questions about a customer's orders should match the orders_by_customer template."""
    repo = SqlTemplateRepository()
    template = repo.find_best_match("Show all orders for customer John Smith.")
    assert template is not None
    assert template.name == "orders_by_customer"


def test_matches_shipment_status():
    """Questions about pending shipments should match the shipment_status template."""
    repo = SqlTemplateRepository()
    template = repo.find_best_match("List pending shipments.")
    assert template is not None
    assert template.name == "shipment_status"


def test_matches_top_customers():
    """Threshold-based customer questions should match top_customers."""
    repo = SqlTemplateRepository()
    template = repo.find_best_match("Which customers have orders above $5,000?")
    assert template is not None
    assert template.name == "top_customers"


def test_no_match_returns_none():
    """An unrelated question should not match any template."""
    repo = SqlTemplateRepository()
    template = repo.find_best_match("What's the weather like today?")
    assert template is None
