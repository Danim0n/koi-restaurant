"""Modelo de mesa del restaurante."""
from sqlalchemy import Boolean, Column, Integer, String

from backend.database import Base


class Table(Base):
    """Mesa física del restaurante."""

    __tablename__ = "tables"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, unique=True, nullable=False)
    capacity = Column(Integer, nullable=False)
    location = Column(String, nullable=True)  # Ej: "Interior", "Terraza", "Barra"
    is_active = Column(Boolean, default=True, nullable=False)
