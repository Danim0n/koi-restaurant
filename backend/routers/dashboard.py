"""Router del dashboard de administración (protegido)."""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth.jwt_handler import get_current_admin
from backend.database import get_db
from backend.models.user import User
from backend.schemas.reservation import ReservationResponse
from backend.services import reservation_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
def obtener_estadisticas(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Devuelve métricas globales del restaurante."""
    return reservation_service.estadisticas_dashboard(db)


@router.get("/reservations/today", response_model=List[ReservationResponse])
def reservas_hoy(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Reservas del día actual."""
    return reservation_service.reservas_de_hoy(db)


@router.get("/reservations/upcoming", response_model=List[ReservationResponse])
def reservas_proximas(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Próximas reservas activas."""
    return reservation_service.reservas_proximas(db)
