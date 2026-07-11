"""Router de autenticación."""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.jwt_handler import (
    create_access_token,
    get_current_user,
    verify_password,
)
from backend.config.settings import settings
from backend.database import get_db
from backend.models.user import User
from backend.schemas.user import LoginRequest, Token, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@router.post("/login", response_model=Token)
def login(datos: LoginRequest, db: Session = Depends(get_db)):
    """Autentica a un usuario y devuelve un JWT."""
    user = db.query(User).filter(User.email == datos.email).first()
    if not user or not verify_password(datos.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta está desactivada",
        )

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "is_admin": user.is_admin},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=token, token_type="bearer", user=user)


@router.get("/me", response_model=UserResponse)
def leer_usuario_actual(current_user: User = Depends(get_current_user)):
    """Devuelve los datos del usuario autenticado."""
    return current_user
