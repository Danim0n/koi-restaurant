"""Modelo de usuario (administradores del panel)."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from backend.database import Base


class User(Base):
    """Usuario del sistema. Solo los admins acceden al panel de gestión."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
