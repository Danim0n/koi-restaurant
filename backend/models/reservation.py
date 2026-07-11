"""Modelo de reserva."""
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Reservation(Base):
    """Reserva de mesa realizada por un cliente."""

    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    customer_email = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    date = Column(String, nullable=False)  # formato YYYY-MM-DD
    time = Column(String, nullable=False)  # formato HH:MM
    guests = Column(Integer, nullable=False)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=True)
    # Estados posibles: pending / confirmed / cancelled / completed
    status = Column(String, default="pending", nullable=False)
    special_requests = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    table = relationship("Table")
