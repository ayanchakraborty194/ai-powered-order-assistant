"""Create schema and seed sample data for the Order Processing database."""

from datetime import datetime, timedelta, timezone

from app.config.log_config import logger
from app.config.postgres_config import postgres_config
from app.models.order_domain_models import (
    Base,
    Customer,
    Order,
    OrderItem,
    Product,
    Shipment,
)


def create_order_db_schema() -> None:
    """Create all order-processing tables if they do not already exist."""
    engine = postgres_config.get_engine()
    Base.metadata.create_all(engine)
    logger.info("Order processing schema created/verified.")


def seed_sample_data(force: bool = False) -> None:
    """Insert a small set of sample rows for demo/testing.

    Args:
        force: If True, wipe and reseed even if data already exists.
    """
    with postgres_config.get_session() as session:
        existing = session.query(Customer).first()
        if existing and not force:
            logger.info("Order DB already seeded; skipping.")
            return

        if force:
            session.query(Shipment).delete()
            session.query(OrderItem).delete()
            session.query(Order).delete()
            session.query(Product).delete()
            session.query(Customer).delete()
            session.commit()

        now = datetime.now(timezone.utc)

        customers = [
            Customer(customer_id=1, customer_name="John Smith", email="john.smith@example.com"),
            Customer(customer_id=2, customer_name="ABC Ltd.", email="orders@abc-ltd.example.com"),
            Customer(customer_id=3, customer_name="Jane Doe", email="jane.doe@example.com"),
        ]

        products = [
            Product(product_id=1, product_name="Wireless Mouse", category="Electronics", price=25.00),
            Product(product_id=2, product_name="Mechanical Keyboard", category="Electronics", price=85.00),
            Product(product_id=3, product_name="USB-C Hub", category="Accessories", price=40.00),
            Product(product_id=4, product_name="Office Chair", category="Furniture", price=220.00),
            Product(product_id=5, product_name="Standing Desk", category="Furniture", price=450.00),
        ]

        orders = [
            Order(
                order_id=10453,
                customer_id=2,
                order_date=now - timedelta(days=3),
                status="Shipped",
                total_amount=310.00,
            ),
            Order(
                order_id=20015,
                customer_id=1,
                order_date=now - timedelta(days=10),
                status="Delivered",
                total_amount=110.00,
            ),
            Order(
                order_id=100234,
                customer_id=3,
                order_date=now - timedelta(days=1),
                status="Pending",
                total_amount=470.00,
            ),
            Order(
                order_id=100235,
                customer_id=2,
                order_date=now - timedelta(days=35),
                status="Delivered",
                total_amount=6200.00,
            ),
        ]

        order_items = [
            OrderItem(order_item_id=1, order_id=10453, product_id=4, quantity=1, unit_price=220.00),
            OrderItem(order_item_id=2, order_id=10453, product_id=3, quantity=1, unit_price=40.00),
            OrderItem(order_item_id=3, order_id=10453, product_id=1, quantity=2, unit_price=25.00),
            OrderItem(order_item_id=4, order_id=20015, product_id=2, quantity=1, unit_price=85.00),
            OrderItem(order_item_id=5, order_id=20015, product_id=1, quantity=1, unit_price=25.00),
            OrderItem(order_item_id=6, order_id=100234, product_id=5, quantity=1, unit_price=450.00),
            OrderItem(order_item_id=7, order_id=100234, product_id=1, quantity=1, unit_price=25.00) ,
            OrderItem(order_item_id=8, order_id=100235, product_id=5, quantity=10, unit_price=450.00),
            OrderItem(order_item_id=9, order_id=100235, product_id=4, quantity=8, unit_price=220.00),
        ]

        shipments = [
            Shipment(
                shipment_id=1,
                order_id=10453,
                carrier="FedEx",
                tracking_number="FX1029384756",
                delivery_status="Delivered",
                shipped_date=now - timedelta(days=1),
                delivered_date=now,
            ),
            Shipment(
                shipment_id=2,
                order_id=20015,
                carrier="UPS",
                tracking_number="UP9384756102",
                delivery_status="Delivered",
                shipped_date=now - timedelta(days=8),
                delivered_date=now - timedelta(days=6),
            ),
            Shipment(
                shipment_id=3,
                order_id=100234,
                carrier=None,
                tracking_number=None,
                delivery_status="Pending",
                shipped_date=None,
                delivered_date=None,
            ),
            Shipment(
                shipment_id=4,
                order_id=100235,
                carrier="DHL",
                tracking_number="DH1122334455",
                delivery_status="Delivered",
                shipped_date=now - timedelta(days=34),
                delivered_date=now - timedelta(days=30),
            ),
        ]

        session.add_all(customers)
        session.add_all(products)
        session.add_all(orders)
        session.add_all(order_items)
        session.add_all(shipments)
        session.commit()
        logger.info("Order DB seeded with sample data.")


if __name__ == "__main__":
    create_order_db_schema()
    seed_sample_data()
