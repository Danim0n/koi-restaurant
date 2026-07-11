"""Lógica de negocio de los pedidos (delivery & takeaway)."""
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.config.settings import settings
from backend.models.menu import MenuItem
from backend.models.order import Order, OrderItem
from backend.schemas.order import OrderCreate


def _round2(valor: float) -> float:
    """Redondea a 2 decimales evitando errores de coma flotante."""
    return round(valor + 1e-9, 2)


def build_order(db: Session, data: OrderCreate) -> Order:
    """Crea un pedido validando los platos y recalculando los precios.

    Nunca se confía en los precios del frontend: se leen de la base de datos.
    El pedido se crea con payment_status="unpaid" y status="pending".
    """
    if not data.items:
        raise HTTPException(status_code=400, detail="El carrito está vacío.")

    # Agrupar cantidades por id (por si llega el mismo plato repetido)
    cantidades: dict[int, int] = {}
    for linea in data.items:
        cantidades[linea.menu_item_id] = (
            cantidades.get(linea.menu_item_id, 0) + linea.quantity
        )

    ids = list(cantidades.keys())
    platos = db.query(MenuItem).filter(MenuItem.id.in_(ids)).all()
    platos_por_id = {p.id: p for p in platos}

    order_items: List[OrderItem] = []
    subtotal = 0.0

    for item_id, cantidad in cantidades.items():
        plato = platos_por_id.get(item_id)
        if plato is None:
            raise HTTPException(
                status_code=400,
                detail=f"El plato con id {item_id} no existe.",
            )
        if not plato.is_available:
            raise HTTPException(
                status_code=400,
                detail=f"«{plato.name}» no está disponible en este momento.",
            )

        linea_subtotal = _round2(plato.price * cantidad)
        subtotal += linea_subtotal
        order_items.append(
            OrderItem(
                menu_item_id=plato.id,
                name=plato.name,
                unit_price=plato.price,
                quantity=cantidad,
                subtotal=linea_subtotal,
            )
        )

    subtotal = _round2(subtotal)
    delivery_fee = settings.DELIVERY_FEE if data.order_type == "delivery" else 0.0
    total = _round2(subtotal + delivery_fee)

    pedido = Order(
        customer_name=data.customer_name.strip(),
        customer_email=data.customer_email,
        customer_phone=data.customer_phone.strip(),
        order_type=data.order_type,
        address=(data.address or "").strip() or None,
        notes=(data.notes or "").strip() or None,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=total,
        status="pending",
        payment_status="unpaid",
        items=order_items,
    )

    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    return pedido


def get_order(db: Session, order_id: int) -> Optional[Order]:
    return db.query(Order).filter(Order.id == order_id).first()


def get_order_by_session(db: Session, session_id: str) -> Optional[Order]:
    return db.query(Order).filter(Order.stripe_session_id == session_id).first()


def list_orders(
    db: Session,
    status_filter: Optional[str] = None,
    payment_filter: Optional[str] = None,
) -> List[Order]:
    query = db.query(Order)
    if status_filter:
        query = query.filter(Order.status == status_filter)
    if payment_filter:
        query = query.filter(Order.payment_status == payment_filter)
    return query.order_by(Order.created_at.desc()).all()


def mark_paid(db: Session, order: Order, payment_intent: Optional[str] = None) -> Order:
    """Marca un pedido como pagado (idempotente) y lo pone en preparación."""
    if order.payment_status != "paid":
        order.payment_status = "paid"
        if order.status == "pending":
            order.status = "preparing"
        if payment_intent:
            order.stripe_payment_intent = payment_intent
        db.commit()
        db.refresh(order)
    return order


def update_order(
    db: Session,
    order_id: int,
    status_value: Optional[str] = None,
    payment_value: Optional[str] = None,
) -> Optional[Order]:
    order = get_order(db, order_id)
    if not order:
        return None
    if status_value:
        order.status = status_value
    if payment_value:
        order.payment_status = payment_value
    db.commit()
    db.refresh(order)
    return order


def delete_order(db: Session, order_id: int) -> bool:
    order = get_order(db, order_id)
    if not order:
        return False
    db.delete(order)
    db.commit()
    return True
