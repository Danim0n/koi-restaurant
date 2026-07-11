"""Inicialización (bootstrap) de la aplicación Koi.

⚠️  Ya NO contiene datos mockeados de demostración (platos ni reservas).
La aplicación es 100 % dinámica: el menú, las reservas y los pedidos se
gestionan exclusivamente desde la base de datos a través del panel admin.

Este script solo crea la ESTRUCTURA mínima imprescindible para poder operar:

  1. Usuario administrador (necesario para acceder al panel).
  2. Categorías del menú vacías (necesarias para poder dar de alta platos
     desde el panel; son la estructura de la carta, no contenido de ejemplo).
  3. Mesas del restaurante (necesarias para la gestión de aforo/reservas).

Se ejecuta automáticamente en el startup si la base de datos está vacía, y
también puede lanzarse manualmente:

    python seed_data.py
"""
from sqlalchemy.orm import Session

from backend.auth.jwt_handler import hash_password
from backend.config.settings import settings
from backend.database import Base, SessionLocal, engine
from backend.models.menu import MenuCategory
from backend.models.table import Table
from backend.models.user import User


# ---------------------------------------------------------------------------
# Estructura mínima (NO son datos de ejemplo, son la estructura del negocio)
# ---------------------------------------------------------------------------
CATEGORIAS = [
    ("Entrantes", "entrantes", "Pequeños bocados para comenzar el viaje.", 1),
    ("Sushi", "sushi", "Rollos maki y uramaki elaborados al momento.", 2),
    ("Nigiri", "nigiri", "Bolas de arroz avinagrado coronadas con pescado.", 3),
    ("Sashimi", "sashimi", "Cortes puros de pescado y marisco de temporada.", 4),
    ("Ramen", "ramen", "Caldos reconfortantes cocinados durante horas.", 5),
    ("Arroces", "arroces", "Especialidades de arroz japonés.", 6),
    ("Postres", "postres", "Dulces delicados de inspiración nipona.", 7),
    ("Bebidas", "bebidas", "Sake, té y coctelería de autor.", 8),
]

MESAS = [
    (1, 2, "Barra"),
    (2, 2, "Barra"),
    (3, 4, "Interior"),
    (4, 4, "Interior"),
    (5, 6, "Interior"),
    (6, 6, "Terraza"),
    (7, 8, "Terraza"),
    (8, 10, "Sala privada"),
]


# ---------------------------------------------------------------------------
# Lógica de inicialización
# ---------------------------------------------------------------------------
def base_vacia(db: Session) -> bool:
    """Comprueba si aún no se ha inicializado la estructura básica."""
    return db.query(User).count() == 0


def bootstrap(db: Session) -> None:
    """Inserta la estructura mínima imprescindible de forma segura."""
    # 1) Usuario administrador (Solo si no existe ya)
    admin_exists = db.query(User).filter_by(email=settings.ADMIN_EMAIL).first()
    if not admin_exists:
        admin = User(
            email=settings.ADMIN_EMAIL,
            name=settings.ADMIN_NAME,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            is_active=True,
            is_admin=True,
        )
        db.add(admin)

    # 2) Categorías del menú (Solo se añaden si el slug NO existe ya)
    for nombre, slug, descripcion, orden in CATEGORIAS:
        cat_exists = db.query(MenuCategory).filter_by(slug=slug).first()
        if not cat_exists:
            db.add(
                MenuCategory(
                    name=nombre, slug=slug, description=descripcion, order_index=orden
                )
            )

    # 3) Mesas del restaurante (Solo si la tabla está vacía)
    if db.query(Table).count() == 0:
        for numero, capacidad, ubicacion in MESAS:
            db.add(Table(number=numero, capacity=capacidad, location=ubicacion))

    db.commit()


def init_db(force: bool = False) -> None:
    """Crea las tablas y la estructura mínima si la base está vacía."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if force or base_vacia(db):
            bootstrap(db)
            print("✅ Base de datos inicializada (admin, categorías y mesas).")
        else:
            print("ℹ️  La base de datos ya está inicializada. Bootstrap omitido.")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
