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

# Configuración de negocio para Koi
DURACION_RESERVA_MINUTOS = 90


def _capacidad_total(db: Session) -> int:
    """Suma la capacidad de todas las mesas activas."""
    total = (
        db.query(func.coalesce(func.sum(Table.capacity), 0))
        .filter(Table.is_active.is_(True))
        .scalar()
    )
    return int(total or 0)


def _obtener_rango_conflicto(hora_reserva_str: str) -> tuple[str, str]:
    """Calcula el intervalo de tiempo en el que no puede solaparse otra reserva.
    
    Si una reserva entra a las 13:30, durará hasta las 15:00.
    Cualquier otra reserva entre las 12:01 y las 14:59 generaría un conflicto en esa mesa.
    """
    dt = datetime.strptime(hora_reserva_str, "%H:%M")
    
    # Restamos y sumamos (duración - 1 minuto) para que los límites del 'between' sean estrictos
    t_min = (dt - timedelta(minutes=DURACION_RESERVA_MINUTOS - 1)).strftime("%H:%M")
    t_max = (dt + timedelta(minutes=DURACION_RESERVA_MINUTOS - 1)).strftime("%H:%M")
    return t_min, t_max


def comensales_reservados(db: Session, fecha: str, hora: str) -> int:
    """Número de comensales ya reservados que coinciden en esa franja de 90 min."""
    t_min, t_max = _obtener_rango_conflicto(hora)
    total = (
        db.query(func.coalesce(func.sum(Reservation.guests), 0))
        .filter(
            Reservation.date == fecha,
            Reservation.time.between(t_min, t_max),  # Protege todo el rango de tiempo de la reserva
            Reservation.status.in_(ESTADOS_ACTIVOS),
        )
        .scalar()
    )
    return int(total or 0)


def comprobar_disponibilidad(db: Session, fecha: str, hora: str, guests: int) -> dict:
    """Comprueba la disponibilidad real verificando si queda alguna mesa física compatible."""
    hoy = date_cls.today()
    hoy_str = hoy.isoformat()

    # 1) Validación de hora pasada
    if fecha == hoy_str:
        ahora_str = datetime.now().strftime("%H:%M")
        if hora < ahora_str:
            return {
                "available": False,
                "message": "Lo sentimos, no se pueden realizar reservas para una hora que ya ha pasado.",
                "remaining_capacity": 0
            }

    # 2) Validación basada en asignación de mesas reales (Best-fit simulado)
    mesa_disponible_id = _asignar_mesa(db, fecha, hora, guests)

    if mesa_disponible_id is not None:
        return {
            "available": True,
            "message": "¡Hay disponibilidad para su reserva!",
            "remaining_capacity": guests, # Retornamos el grupo ya que hay mesa física viable
        }
        
    return {
        "available": False,
        "message": "Lo sentimos, no queda ninguna mesa disponible para ese número de comensales en esta franja.",
        "remaining_capacity": 0,
    }

def obtener_mapa_horas_disponibles(db: Session, fecha: str, guests: int) -> dict:
    """Devuelve el estado exacto de los botones del formulario usando simulación de mesas."""
    todas_las_horas = [
        "12:00", "12:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30",
        "20:00", "20:30", "21:00", "21:30", "22:00", "22:30"
    ]
    
    mapa_disponibilidad = {}
    hoy_str = date_cls.today().isoformat()
    ahora_str = datetime.now().strftime("%H:%M")

    for h in todas_las_horas:
        if fecha == hoy_str and h < ahora_str:
            mapa_disponibilidad[h] = False
            continue
            
        mesa_id = _asignar_mesa(db, fecha, h, guests)
        mapa_disponibilidad[h] = mesa_id is not None

    return mapa_disponibilidad


def _asignar_mesa(db: Session, fecha: str, hora: str, guests: int) -> Optional[int]:
    """Asigna la mesa libre más pequeña que no tenga reservas activas en esa franja de tiempo."""
    t_min, t_max = _obtener_rango_conflicto(hora)
    
    # Buscamos qué IDs de mesa están ocupados en este rango de 90 minutos
    mesas_ocupadas = {
        r.table_id
        for r in db.query(Reservation.table_id)
        .filter(
            Reservation.date == fecha,
            Reservation.time.between(t_min, t_max),  # Solapamiento temporal protegido
            Reservation.status.in_(ESTADOS_ACTIVOS),
            Reservation.table_id.isnot(None),
        )
        .all()
    }
    
    # Algoritmo Best-fit: Filtra y ordena por capacidad ascendente
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
    """Crea una reserva asignando mesa y confirmando automáticamente si hay sitio.
    
    - Grupos normales (hasta 6 comensales): Se confirma automáticamente ("confirmed").
    - Grupos grandes (más de 6 comensales): Queda pendiente de revisión manual ("pending").
    """
    table_id = _asignar_mesa(db, data.date, data.time, data.guests)
    
    # Decidimos el estado según el tamaño del grupo (Enfoque Híbrido)
    if data.guests <= 6:
        nuevo_estado = "confirmed"
    else:
        nuevo_estado = "pending"

    # Si por algún motivo no hay mesa física libre, NUNCA la confirmamos automáticamente, pasa a pendiente para que la revises en el dashboard.
    if not table_id:
        nuevo_estado = "pending"
        
    reserva = Reservation(
        **data.model_dump(),
        table_id=table_id,
        status=nuevo_estado,
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
        db.query(func.count(func.distinct(Reservation.id)))
        .filter(Reservation.date >= inicio_semana, Reservation.date <= fin_semana)
        .scalar()
    )
    total_clientes = (
        db.query(func.count(func.distinct(Reservation.customer_email))).scalar()
    )

    capacidad = _capacidad_total(db)
    
    # Comensales totales activos del día de hoy
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
        .filter(Reservation.date > hoy_str, Reservation.status.in_(ESTADOS_ACTIVOS))
        .order_by(Reservation.date.asc(), Reservation.time.asc())
        .limit(limite)
        .all()
    )