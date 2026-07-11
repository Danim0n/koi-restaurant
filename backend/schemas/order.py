"""Schemas Pydantic para pedidos (delivery & takeaway)."""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


# ---------------------------------------------------------------------------
# Líneas del pedido
# ---------------------------------------------------------------------------
class OrderItemInput(BaseModel):
    """Línea que envía el carrito del frontend (solo id y cantidad)."""

    menu_item_id: int
    quantity: int = Field(gt=0, le=50)


class OrderItemResponse(BaseModel):
    id: int
    menu_item_id: Optional[int] = None
    name: str
    unit_price: float
    quantity: int
    subtotal: float

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Pedido
# ---------------------------------------------------------------------------
class OrderCreate(BaseModel):
    """Datos que envía el cliente para crear un pedido y pagarlo."""

    customer_name: str = Field(min_length=2, max_length=120)
    customer_email: EmailStr
    customer_phone: str = Field(min_length=6, max_length=30)
    order_type: Literal["delivery", "takeaway"] = "delivery"
    address: Optional[str] = None
    notes: Optional[str] = None
    items: List[OrderItemInput] = Field(min_length=1)

    @model_validator(mode="after")
    def validar_direccion(self):
        """La dirección es obligatoria para pedidos a domicilio."""
        if self.order_type == "delivery" and not (self.address and self.address.strip()):
            raise ValueError("La dirección es obligatoria para pedidos a domicilio.")
        return self


class OrderStatusUpdate(BaseModel):
    """Actualización de estado del pedido (admin)."""

    status: Optional[
        Literal[
            "pending",
            "preparing",
            "ready",
            "out_for_delivery",
            "delivered",
            "cancelled",
        ]
    ] = None
    payment_status: Optional[Literal["unpaid", "paid", "refunded"]] = None


class OrderResponse(BaseModel):
    id: int
    customer_name: str
    customer_email: str
    customer_phone: str
    order_type: str
    address: Optional[str] = None
    notes: Optional[str] = None
    subtotal: float
    delivery_fee: float
    total: float
    status: str
    payment_status: str
    stripe_session_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class CheckoutResponse(BaseModel):
    """Respuesta al crear la sesión de pago de Stripe."""

    order_id: int
    checkout_url: str
    session_id: str
