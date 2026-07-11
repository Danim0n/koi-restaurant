"""Modelos de pedidos a domicilio / para recoger (delivery & takeaway)."""
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Order(Base):
    """Pedido realizado desde la web (delivery o takeaway)."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    # Datos del cliente
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False, index=True)
    customer_phone = Column(String, nullable=False)

    # Tipo de pedido: "delivery" (a domicilio) o "takeaway" (recoger)
    order_type = Column(String, nullable=False, default="delivery")
    # Dirección de entrega (obligatoria solo para delivery)
    address = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Importes (en euros)
    subtotal = Column(Float, nullable=False, default=0.0)
    delivery_fee = Column(Float, nullable=False, default=0.0)
    total = Column(Float, nullable=False, default=0.0)

    # Estado del pedido: pending / preparing / ready / out_for_delivery /
    # delivered / cancelled
    status = Column(String, nullable=False, default="pending", index=True)

    # Estado del pago: unpaid / paid / refunded
    payment_status = Column(String, nullable=False, default="unpaid", index=True)

    # Referencias de Stripe
    stripe_session_id = Column(String, nullable=True, index=True)
    stripe_payment_intent = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    """Línea de un pedido. Guarda una instantánea de nombre y precio."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=True)

    # Instantánea del plato en el momento del pedido
    name = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    subtotal = Column(Float, nullable=False, default=0.0)

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem")
