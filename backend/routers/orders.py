"""Router de pedidos: creación, pasarela de pago Stripe y webhook."""
from typing import List, Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from backend.auth.jwt_handler import get_current_admin
from backend.config.settings import settings
from backend.database import get_db
from backend.models.user import User
from backend.schemas.order import (
    CheckoutResponse,
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
)
from backend.services import order_service

router = APIRouter(prefix="/api/orders", tags=["Pedidos"])

# Configuración de la clave secreta de Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


# ---------------------------------------------------------------------------
# Público: crear pedido + sesión de pago
# ---------------------------------------------------------------------------
@router.post("/checkout", response_model=CheckoutResponse, status_code=201)
def crear_checkout(datos: OrderCreate, db: Session = Depends(get_db)):
    """Crea el pedido en la base de datos y genera una Stripe Checkout Session si es Online.
    
    Si es pago en mano, guarda el pedido directamente y devuelve la URL de éxito local.
    """
    # 1) Crear el pedido validando platos y recalculando precios en el servidor
    # NOTA: Si tu modelo de base de datos no tiene una columna para 'payment_method',
    # pasarlo en 'datos' no romperá nada si tu build_order solo extrae lo necesario.
    pedido = order_service.build_order(db, datos)

    # 2) SI EL PAGO ES EN MANO: Nos saltamos Stripe por completo
    if datos.payment_method == "cash_card":
        db.commit() # Aseguramos que se guarde el pedido en la BD
        return CheckoutResponse(
            order_id=pedido.id,
            checkout_url=f"{settings.BASE_URL}/pedido/exito?order_id={pedido.id}",
            session_id=None
        )

    # 3) SI EL PAGO ES ONLINE: Ejecuta Stripe con normalidad
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="La pasarela de pago no está configurada. Añade STRIPE_SECRET_KEY.",
        )

    # Construir las líneas para Stripe (importes en céntimos)
    line_items = []
    for item in pedido.items:
        line_items.append(
            {
                "price_data": {
                    "currency": settings.STRIPE_CURRENCY,
                    "product_data": {"name": item.name},
                    "unit_amount": int(round(item.unit_price * 100)),
                },
                "quantity": item.quantity,
            }
        )

    if pedido.delivery_fee and pedido.delivery_fee > 0:
        line_items.append(
            {
                "price_data": {
                    "currency": settings.STRIPE_CURRENCY,
                    "product_data": {"name": "Gastos de envío"},
                    "unit_amount": int(round(pedido.delivery_fee * 100)),
                },
                "quantity": 1,
            }
        )

    try:
        sesion = stripe.checkout.Session.create(
            mode="payment",
            line_items=line_items,
            customer_email=pedido.customer_email,
            client_reference_id=str(pedido.id),
            metadata={"order_id": str(pedido.id)},
            success_url=(
                f"{settings.BASE_URL}/pedido/exito"
                "?session_id={CHECKOUT_SESSION_ID}"
            ),
            cancel_url=f"{settings.BASE_URL}/pedido/cancelado?order_id={pedido.id}",
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502, detail=f"Error al crear la sesión de pago: {exc}"
        )

    pedido.stripe_session_id = sesion.id
    db.commit()

    return CheckoutResponse(
        order_id=pedido.id,
        checkout_url=sesion.url,
        session_id=sesion.id,
    )

@router.get("/by-session/{session_id}", response_model=OrderResponse)
def obtener_pedido_por_sesion(session_id: str, db: Session = Depends(get_db)):
    """Permite a la página de éxito consultar el estado del pedido."""
    pedido = order_service.get_order_by_session(db, session_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido


# ---------------------------------------------------------------------------
# Webhook de Stripe
# ---------------------------------------------------------------------------
@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Escucha los eventos de Stripe y marca los pedidos como pagados.

    Verifica la firma con STRIPE_WEBHOOK_SECRET cuando está configurado.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        if settings.STRIPE_WEBHOOK_SECRET:
            evento = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        else:
            # Sin secreto configurado: parseo directo (solo para desarrollo)
            import json

            evento = json.loads(payload)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise HTTPException(status_code=400, detail=f"Webhook inválido: {exc}")

    tipo = evento["type"] if isinstance(evento, dict) else evento.type

    if tipo == "checkout.session.completed":
        sesion = (
            evento["data"]["object"]
            if isinstance(evento, dict)
            else evento.data.object
        )
        session_id = sesion.get("id")
        payment_intent = sesion.get("payment_intent")
        order_id = (sesion.get("metadata") or {}).get("order_id")

        pedido = None
        if order_id:
            pedido = order_service.get_order(db, int(order_id))
        if pedido is None and session_id:
            pedido = order_service.get_order_by_session(db, session_id)

        if pedido:
            order_service.mark_paid(db, pedido, payment_intent)

    return {"received": True}


# ---------------------------------------------------------------------------
# Administración (protegido)
# ---------------------------------------------------------------------------
@router.get("", response_model=List[OrderResponse])
def listar_pedidos(
    status_filter: Optional[str] = Query(None, alias="status"),
    payment_filter: Optional[str] = Query(None, alias="payment_status"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Lista todos los pedidos (solo admin)."""
    return order_service.list_orders(db, status_filter, payment_filter)


@router.get("/{order_id}", response_model=OrderResponse)
def obtener_pedido(
    order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    pedido = order_service.get_order(db, order_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido


@router.put("/{order_id}", response_model=OrderResponse)
def actualizar_pedido(
    order_id: int,
    datos: OrderStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    pedido = order_service.update_order(
        db, order_id, datos.status, datos.payment_status
    )
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido


@router.delete("/{order_id}", status_code=status.HTTP_200_OK)
def eliminar_pedido(
    order_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    if not order_service.delete_order(db, order_id):
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"detail": "Pedido eliminado correctamente"}
