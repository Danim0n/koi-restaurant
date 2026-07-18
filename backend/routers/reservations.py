"""Router de reservas (público + gestión admin)."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.auth.jwt_handler import get_current_admin
from backend.database import get_db
from backend.models.user import User
from backend.schemas.reservation import (
    AvailabilityResponse,
    ReservationCreate,
    ReservationResponse,
    ReservationUpdate,
)
from backend.services import reservation_service
from datetime import datetime 

router = APIRouter(prefix="/api/reservations", tags=["Reservas"])



@router.get("/availability", response_model=AvailabilityResponse)
def comprobar_disponibilidad(
    date: str = Query(...),
    time: str = Query(...),
    guests: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
):
    """Comprueba la disponibilidad para una fecha/hora/comensales."""
    # Validación de cierre los martes (1 = Martes en Python)
    try:
        fecha_obj = datetime.strptime(date, "%Y-%m-%d").date()
        if fecha_obj.weekday() == 1:
            return {
                "available": False,
                "message": "El restaurante permanece cerrado los martes por descanso.Perdone las molestias"
            }
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use AAAA-MM-DD.")

    resultado = reservation_service.comprobar_disponibilidad(db, date, time, guests)
    return resultado


@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def crear_reserva(datos: ReservationCreate, db: Session = Depends(get_db)):
    """Crea una reserva (endpoint público)."""
    # Validación de seguridad en el backend por si se saltan el JS (1 = Martes en Python)
    try:
        fecha_obj = datetime.strptime(datos.date, "%Y-%m-%d").date()
        if fecha_obj.weekday() == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="El restaurante permanece cerrado los martes por descanso. Perdone las molestias"
            )
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use AAAA-MM-DD.")

    disponibilidad = reservation_service.comprobar_disponibilidad(
        db, datos.date, datos.time, datos.guests
    )
    if not disponibilidad["available"]:
        raise HTTPException(status_code=409, detail=disponibilidad["message"])
    return reservation_service.crear_reserva(db, datos)

@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def crear_reserva(datos: ReservationCreate, db: Session = Depends(get_db)):
    """Crea una reserva (endpoint público)."""
    disponibilidad = reservation_service.comprobar_disponibilidad(
        db, datos.date, datos.time, datos.guests
    )
    if not disponibilidad["available"]:
        raise HTTPException(status_code=409, detail=disponibilidad["message"])
    return reservation_service.crear_reserva(db, datos)


@router.get("", response_model=List[ReservationResponse])
def listar_reservas(
    status_filter: Optional[str] = Query(None, alias="status"),
    date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Lista todas las reservas (solo admin)."""
    return reservation_service.listar_reservas(db, status_filter, date)


@router.put("/{reserva_id}", response_model=ReservationResponse)
def actualizar_reserva(
    reserva_id: int,
    datos: ReservationUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Actualiza una reserva o su estado (solo admin)."""
    reserva = reservation_service.actualizar_reserva(db, reserva_id, datos)
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return reserva


@router.delete("/{reserva_id}", status_code=status.HTTP_200_OK)
def eliminar_reserva(
    reserva_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Elimina una reserva (solo admin)."""
    if not reservation_service.eliminar_reserva(db, reserva_id):
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return {"detail": "Reserva eliminada correctamente"}
