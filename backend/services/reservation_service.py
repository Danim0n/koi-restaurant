"""Lógica de negocio de las reservas."""
from datetime import date as date_cls
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.reservation import Reservation
from backend.models.table import Table
from backend.schemas.reservation import ReservationCreate, ReservationUpdate

# Estados que ocupan capacidad de forma efectiva
ESTADOS_ACTIVOS = ("pending", "confirmed")


def _capacidad_total(db: Session) -> int:
    """Suma la capacidad de todas las mesas activas."""
    total = (
        db.query(func.coalesce(func.sum(Table.capacity), 0))
        .filter(Table.is_active.is_(True))
        .scalar()
    )
    return int(total or 0)


def comensales_reservados(db: Session, fecha: str, hora: str) -> int:
    """Número de comensales ya reservados en una fecha/hora concretas."""
    total = (
        db.query(func.coalesce(func.sum(Reservation.guests), 0))
        .filter(
            Reservation.date == fecha,
            Reservation.time == hora,
            Reservation.status.in_(ESTADOS_ACTIVOS),
        )
        .scalar()
    )
    return int(total or 0)


def comprobar_disponibilidad(db: Session, fecha: str, hora: str, guests: int) -> dict:
    """Comprueba si hay capacidad para una reserva en fecha/hora dadas."""
    capacidad = _capacidad_total(db)
    ocupados = comensales_reservados(db, fecha, hora)
    restante = capacidad - ocupados

    if guests <= restante:
        return {
            "available": True,
            "message": "¡Hay disponibilidad para su reserva!",
            "remaining_capacity": restante,
        }
    return {
        "available": False,
        "message": (
            "Lo sentimos, no queda disponibilidad para esa franja horaria. "
            "Pruebe con otra hora o fecha."
        ),
        "remaining_capacity": max(restante, 0),
    }


def _asignar_mesa(db: Session, fecha: str, hora: str, guests: int) -> Optional[int]:
    """Asigna la mesa libre más pequeña que acomode a los comensales."""
    mesas_ocupadas = {
        r.table_id
        for r in db.query(Reservation.table_id)
        .filter(
            Reservation.date == fecha,
            Reservation.time == hora,
            Reservation.status.in_(ESTADOS_ACTIVOS),
            Reservation.table_id.isnot(None),
        )
        .all()
    }
    mesas = (
        db.query(Table)
        .filter(Table.is_active.is_(True), Table.capacity >= guests)
        .order_by(Table.capacity.asc())
        .all()
    )
    for mesa in mesas:
        if mesa.id not in mesas_ocupadas:
            return mesa.id
    return None


def crear_reserva(db: Session, data: ReservationCreate) -> Reservation:
    """Crea una reserva asignando mesa automáticamente si es posible."""
    table_id = _asignar_mesa(db, data.date, data.time, data.guests)
    reserva = Reservation(
        **data.model_dump(),
        table_id=table_id,
        status="pending",
    )
    db.add(reserva)
    db.commit()
    db.refresh(reserva)
    return reserva


def listar_reservas(
    db: Session,
    status: Optional[str] = None,
    fecha: Optional[str] = None,
) -> List[Reservation]:
    query = db.query(Reservation)
    if status:
        query = query.filter(Reservation.status == status)
    if fecha:
        query = query.filter(Reservation.date == fecha)
    return query.order_by(Reservation.date.desc(), Reservation.time.desc()).all()


def obtener_reserva(db: Session, reserva_id: int) -> Optional[Reservation]:
    return db.query(Reservation).filter(Reservation.id == reserva_id).first()


def actualizar_reserva(
    db: Session, reserva_id: int, data: ReservationUpdate
) -> Optional[Reservation]:
    reserva = obtener_reserva(db, reserva_id)
    if not reserva:
        return None
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(reserva, campo, valor)
    db.commit()
    db.refresh(reserva)
    return reserva


def eliminar_reserva(db: Session, reserva_id: int) -> bool:
    reserva = obtener_reserva(db, reserva_id)
    if not reserva:
        return False
    db.delete(reserva)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# Estadísticas para el dashboard
# ---------------------------------------------------------------------------
def estadisticas_dashboard(db: Session) -> dict:
    """Calcula las métricas mostradas en el dashboard de administración."""
    hoy = date_cls.today()
    hoy_str = hoy.isoformat()
    inicio_semana = (hoy - timedelta(days=hoy.weekday())).isoformat()
    fin_semana = (hoy + timedelta(days=6 - hoy.weekday())).isoformat()

    reservas_hoy = (
        db.query(func.count(Reservation.id))
        .filter(Reservation.date == hoy_str)
        .scalar()
    )
    reservas_semana = (
        db.query(func.count(Reservation.id))
        .filter(Reservation.date >= inicio_semana, Reservation.date <= fin_semana)
        .scalar()
    )
    total_clientes = (
        db.query(func.count(func.distinct(Reservation.customer_email))).scalar()
    )

    capacidad = _capacidad_total(db)
    comensales_hoy = (
        db.query(func.coalesce(func.sum(Reservation.guests), 0))
        .filter(
            Reservation.date == hoy_str,
            Reservation.status.in_(ESTADOS_ACTIVOS),
        )
        .scalar()
    )
    ocupacion = round((comensales_hoy / capacidad) * 100) if capacidad else 0

    return {
        "reservas_hoy": int(reservas_hoy or 0),
        "reservas_semana": int(reservas_semana or 0),
        "total_clientes": int(total_clientes or 0),
        "ocupacion": min(int(ocupacion), 100),
    }


def reservas_de_hoy(db: Session) -> List[Reservation]:
    hoy_str = date_cls.today().isoformat()
    return (
        db.query(Reservation)
        .filter(Reservation.date == hoy_str)
        .order_by(Reservation.time.asc())
        .all()
    )


def reservas_proximas(db: Session, limite: int = 10) -> List[Reservation]:
    hoy_str = date_cls.today().isoformat()
    return (
        db.query(Reservation)
        .filter(Reservation.date >= hoy_str, Reservation.status.in_(ESTADOS_ACTIVOS))
        .order_by(Reservation.date.asc(), Reservation.time.asc())
        .limit(limite)
        .all()
    )
