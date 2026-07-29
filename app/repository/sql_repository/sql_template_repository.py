"""Repository of predefined, pre-validated SQL templates.

This is Layer 2 of the SQL retrieval strategy: before generating SQL with an
LLM, the assistant checks whether a known template already answers a
sufficiently similar class of question.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class SqlTemplate:
    """A named, validated SQL template with its trigger keywords."""

    name: str
    description: str
    sql: str
    keywords: tuple


class SqlTemplateRepository:
    """In-memory repository of validated SQL templates."""

    def __init__(self) -> None:
        """Register all known templates."""
        self._templates: Dict[str, SqlTemplate] = {
            "orders_by_customer": SqlTemplate(
                name="orders_by_customer",
                description="All orders placed by a given customer.",
                sql=(
                    "SELECT o.order_id, o.order_date, o.status, o.total_amount "
                    "FROM orders o "
                    "JOIN customers c ON c.customer_id = o.customer_id "
                    "WHERE c.customer_name ILIKE :customer_name "
                    "ORDER BY o.order_date DESC"
                ),
                keywords=("orders for customer", "orders placed by", "show orders for", "show all orders for"),
            ),
            "order_details": SqlTemplate(
                name="order_details",
                description="Full details (status, items) for a single order by ID.",
                sql=(
                    "SELECT o.order_id, o.status, o.order_date, o.total_amount, "
                    "p.product_name, oi.quantity, oi.unit_price "
                    "FROM orders o "
                    "JOIN order_items oi ON oi.order_id = o.order_id "
                    "JOIN products p ON p.product_id = oi.product_id "
                    "WHERE o.order_id = :order_id"
                ),
                keywords=("order #", "order id", "status of order", "products in order"),
            ),
            "shipment_status": SqlTemplate(
                name="shipment_status",
                description="Shipment/delivery status, optionally filtered by status or customer.",
                sql=(
                    "SELECT o.order_id, c.customer_name, s.carrier, s.tracking_number, "
                    "s.delivery_status, s.shipped_date, s.delivered_date "
                    "FROM shipments s "
                    "JOIN orders o ON o.order_id = s.order_id "
                    "JOIN customers c ON c.customer_id = o.customer_id "
                    "WHERE s.delivery_status ILIKE :delivery_status"
                ),
                keywords=("pending shipments", "delayed shipments", "shipment status", "delivery"),
            ),
            "top_customers": SqlTemplate(
                name="top_customers",
                description="Customers whose total order value exceeds a threshold.",
                sql=(
                    "SELECT c.customer_name, SUM(o.total_amount) AS total_spent "
                    "FROM orders o "
                    "JOIN customers c ON c.customer_id = o.customer_id "
                    "GROUP BY c.customer_name "
                    "HAVING SUM(o.total_amount) > :threshold "
                    "ORDER BY total_spent DESC"
                ),
                keywords=("customers have orders above", "top customers", "highest spending"),
            ),
            "monthly_orders": SqlTemplate(
                name="monthly_orders",
                description="Orders placed within a recent time window (e.g. last month, this week).",
                sql=(
                    "SELECT o.order_id, c.customer_name, o.order_date, o.status, o.total_amount "
                    "FROM orders o "
                    "JOIN customers c ON c.customer_id = o.customer_id "
                    "WHERE o.order_date >= :start_date "
                    "ORDER BY o.order_date DESC"
                ),
                keywords=("orders placed last month", "orders this week", "recent orders"),
            ),
        }

    def list_templates(self) -> List[SqlTemplate]:
        """Return all registered templates.

        Returns:
            List of SqlTemplate.
        """
        return list(self._templates.values())

    def get_template(self, name: str) -> Optional[SqlTemplate]:
        """Fetch a template by its registered name.

        Args:
            name: Template name.

        Returns:
            SqlTemplate or None if not found.
        """
        return self._templates.get(name)

    def find_best_match(self, query: str) -> Optional[SqlTemplate]:
        """Find the template whose keywords best match a NL query.

        Args:
            query: User's natural language question (comparison is
                case-insensitive).

        Returns:
            The best-matching SqlTemplate, or None if no keyword matches.
        """
        normalized = query.lower()
        best_match: Optional[SqlTemplate] = None
        best_score = 0

        for template in self._templates.values():
            # Score by total matched character length (favors longer, more
            # specific phrase matches over generic short keywords) rather
            # than raw match count, to reduce ambiguous ties.
            score = sum(len(kw) for kw in template.keywords if kw in normalized)
            if score > best_score:
                best_score = score
                best_match = template

        return best_match if best_score > 0 else None


sql_template_repository = SqlTemplateRepository()
