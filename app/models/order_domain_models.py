"""SQLAlchemy ORM models for the Order Processing (PostgreSQL) database.

These are distinct from the Pydantic IAM models (User, Role, Component),
which are backed by SQLite. This module defines the business schema the
NL-to-SQL assistant reasons over and queries.
"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for order-processing ORM models."""


class Customer(Base):
    """Customer domain model."""

    __tablename__ = "customers"

    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=True)

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")


class Product(Base):
    """Product catalog model."""

    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(255), nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)


class Order(Base):
    """Order header model."""

    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id"))
    order_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    customer: Mapped["Customer"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")
    shipment: Mapped["Shipment"] = relationship(back_populates="order", uselist=False)


class OrderItem(Base):
    """Line items purchased in an order."""

    __tablename__ = "order_items"

    order_item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class Shipment(Base):
    """Shipment and delivery information for an order."""

    __tablename__ = "shipments"

    shipment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"))
    carrier: Mapped[str] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[str] = mapped_column(String(100), nullable=True)
    delivery_status: Mapped[str] = mapped_column(String(50), nullable=False)
    shipped_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    delivered_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    order: Mapped["Order"] = relationship(back_populates="shipment")
