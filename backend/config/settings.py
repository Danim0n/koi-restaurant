"""Configuración central de la aplicación Koi.

Usa pydantic-settings para leer variables de entorno (o del archivo .env).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación cargada desde variables de entorno."""

    # Seguridad / JWT
    SECRET_KEY: str = "koi-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas

    # Base de datos
    DATABASE_URL: str = "sqlite:///./koi.db"

    # Información del restaurante
    RESTAURANT_NAME: str = "Koi"
    RESTAURANT_ADDRESS: str = "Calle Ejemplo 123, Madrid"
    RESTAURANT_PHONE: str = "+34 91 234 56 78"
    RESTAURANT_EMAIL: str = "hola@koi.es"

    # Credenciales del administrador por defecto (se crean en el bootstrap)
    ADMIN_EMAIL: str = "admin@koi.com"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_NAME: str = "Administrador Koi"

    # URL pública base (usada en las redirecciones de Stripe)
    BASE_URL: str = "http://localhost:8000"

    # ---- Stripe (pasarela de pago) ----
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_CURRENCY: str = "eur"

    # Gastos de envío para pedidos a domicilio (en euros)
    DELIVERY_FEE: float = 3.50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Instancia única reutilizable en toda la aplicación
settings = Settings()
