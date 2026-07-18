"""Punto de entrada de la aplicación Koi (FastAPI).

Sirve la API REST y las páginas HTML (Jinja2 + archivos estáticos).
Ejecutar desde la raíz del proyecto:

    uvicorn backend.main:app --reload
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.config.settings import settings
from backend.routers import auth, dashboard, menu, orders, pages, reservations

# Rutas absolutas al frontend (para funcionar desde cualquier cwd)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")

app = FastAPI(
    title=f"{settings.RESTAURANT_NAME} — API",
    description=(
        "API y web del restaurante japonés premium Koi. "
        "Incluye menú dinámico, reservas y panel de administración."
    ),
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Archivos estáticos
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Templates Jinja2 compartidos con el router de páginas
templates = Jinja2Templates(directory=TEMPLATES_DIR)
pages.set_templates(templates)

# Routers de la API
app.include_router(auth.router)
app.include_router(menu.router)
app.include_router(reservations.router)
app.include_router(dashboard.router)
app.include_router(orders.router)
# Router de páginas HTML (al final para no interferir con la API)
app.include_router(pages.router)


@app.on_event("startup")
def on_startup():
    """Crea las tablas y siembra datos de demostración si es necesario."""
    from seed_data import init_db

    #init_db()


@app.get("/api/health", tags=["Sistema"])
def health_check():
    """Endpoint simple de comprobación de estado."""
    return {"status": "ok", "restaurant": settings.RESTAURANT_NAME}
