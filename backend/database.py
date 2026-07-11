"""Configuración de la base de datos con SQLAlchemy (SQLite).

Expone el engine, la fábrica de sesiones, la base declarativa y la
dependencia `get_db` usada por los routers de FastAPI.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.config.settings import settings

# Para SQLite es necesario desactivar la comprobación de hilo único
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa de la que heredan todos los modelos
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI que entrega una sesión de base de datos.

    Garantiza que la sesión se cierre siempre al finalizar la petición.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
