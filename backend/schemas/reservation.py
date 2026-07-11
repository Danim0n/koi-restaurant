"""Schemas Pydantic para reservas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ReservationBase(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    customer_email: EmailStr
    customer_phone: str = Field(..., min_length=6, max_length=30)
    date: str  # YYYY-MM-DD
    time: str  # HH:MM
    guests: int = Field(..., ge=1, le=12)
    special_requests: Optional[str] = None

    @field_validator("date")
    @classmethod
    def validar_fecha(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("La fecha debe tener el formato YYYY-MM-DD")
        return v

    @field_validator("time")
    @classmethod
    def validar_hora(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("La hora debe tener el formato HH:MM")
        return v


class ReservationCreate(ReservationBase):
    pass


class ReservationUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    guests: Optional[int] = Field(default=None, ge=1, le=12)
    table_id: Optional[int] = None
    status: Optional[str] = None
    special_requests: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validar_estado(cls, v):
        if v is None:
            return v
        permitidos = {"pending", "confirmed", "cancelled", "completed"}
        if v not in permitidos:
            raise ValueError(f"Estado inválido. Debe ser uno de: {permitidos}")
        return v


class ReservationResponse(ReservationBase):
    id: int
    table_id: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AvailabilityResponse(BaseModel):
    available: bool
    message: str
    remaining_capacity: int = 0
