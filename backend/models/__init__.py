"""Modelos de SQLAlchemy de la aplicación Koi.

Se importan todos aquí para que `Base.metadata.create_all` los detecte.
"""
from backend.models.menu import MenuCategory, MenuItem
from backend.models.order import Order, OrderItem
from backend.models.reservation import Reservation
from backend.models.table import Table
from backend.models.user import User

__all__ = [
    "User",
    "MenuCategory",
    "MenuItem",
    "Reservation",
    "Table",
    "Order",
    "OrderItem",
]
