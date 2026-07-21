"""Router de reservas (público + gestión admin)."""
from typing import List, Optional
from datetime import datetime, time  # Añadimos time para validar los turnos

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

router = APIRouter(prefix="/api/reservations", tags=["Reservas"])


def validar_horario_servicio(hora_str: str):
    """Función auxiliar para comprobar que la hora cae en los turnos de Koi."""
    try:
        # Parseamos la hora que llega (ej: "13:30" o "21:00")
        h, m = map(int, hora_str.split(":"))
        hora_obj = time(h, m)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de hora inválido. Use HH:MM.")

    # Turno de Comida: 12:00 a 15:30
    turno_comida = time(12, 0) <= hora_obj <= time(15, 30)
    # Turno de Cena: 20:00 a 22:30
    turno_cena = time(20, 0) <= hora_obj <= time(22, 30)

    if not (turno_comida or turno_cena):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El horario seleccionado está fuera de las horas de servicio (Comidas: 12:00-15:30, Cenas: 20:00-22:30)."
        )


@router.get("/availability")
def comprobar_disponibilidad(
    date: str = Query(...),
    guests: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
):
    """Comprueba y devuelve el mapa de horas disponibles/completas para una fecha."""
    try:
        fecha_obj = datetime.strptime(date, "%Y-%m-%d").date()
        if fecha_obj.weekday() == 1:
            return {
                "error_cierre": True,
                "message": "El restaurante permanece cerrado los martes por descanso. Perdone las molestias."
            }
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use AAAA-MM-DD.")

    resultado = reservation_service.obtener_mapa_horas_disponibles(db, date, guests)
    return resultado


@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def crear_reserva(datos: ReservationCreate, db: Session = Depends(get_db)):
    """Crea una reserva (endpoint público)."""
    # 1) Validación de seguridad de los martes por si se saltan el JS
    try:
        fecha_obj = datetime.strptime(datos.date, "%Y-%m-%d").date()
        if fecha_obj.weekday() == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="El restaurante permanece cerrado los martes por descanso. Perdone las molestias"
            )
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use AAAA-MM-DD.")

    # 2) Validación de seguridad de los turnos horarios
    validar_horario_servicio(datos.time)

    # 3) Comprobación de aforo/mesas disponibles[cite: 14]
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