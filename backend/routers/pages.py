"""Router de páginas HTML renderizadas con Jinja2."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.config.settings import settings
from backend.database import get_db
from backend.services import menu_service

router = APIRouter(tags=["Páginas"])

# Los templates se inyectan desde main.py mediante set_templates()
templates: Jinja2Templates | None = None


def set_templates(t: Jinja2Templates) -> None:
    """Permite a main.py compartir la instancia de templates."""
    global templates
    templates = t


def _contexto_base(request: Request) -> dict:
    """Contexto común disponible en todas las plantillas."""
    return {
        "request": request,
        "restaurant": {
            "name": settings.RESTAURANT_NAME,
            "address": settings.RESTAURANT_ADDRESS,
            "phone": settings.RESTAURANT_PHONE,
            "email": settings.RESTAURANT_EMAIL,
        },
    }


@router.get("/", response_class=HTMLResponse)
def pagina_inicio(request: Request, db: Session = Depends(get_db)):
    """Landing page principal."""
    destacados = menu_service.get_items(db, featured=True)
    contexto = _contexto_base(request)
    contexto["featured_items"] = [menu_service.serialize_item(i) for i in destacados][:4]
    return templates.TemplateResponse("index.html", contexto)


@router.get("/menu", response_class=HTMLResponse)
def pagina_menu(request: Request):
    """Página del menú (los datos se cargan por JS)."""
    return templates.TemplateResponse("menu.html", _contexto_base(request))


@router.get("/reservas", response_class=HTMLResponse)
def pagina_reservas(request: Request):
    """Página del formulario de reservas."""
    return templates.TemplateResponse("reservations.html", _contexto_base(request))


@router.get("/pedido/exito", response_class=HTMLResponse)
def pagina_pedido_exito(request: Request):
    """Página de confirmación tras un pago correcto en Stripe."""
    return templates.TemplateResponse("order_success.html", _contexto_base(request))


@router.get("/pedido/cancelado", response_class=HTMLResponse)
def pagina_pedido_cancelado(request: Request):
    """Página mostrada cuando el cliente cancela el pago."""
    return templates.TemplateResponse("order_cancel.html", _contexto_base(request))


# ---------------------------------------------------------------------------
# Panel de administración
# ---------------------------------------------------------------------------
@router.get("/admin", response_class=HTMLResponse)
def admin_login(request: Request):
    """Página de login del panel admin."""
    return templates.TemplateResponse("admin/login.html", _contexto_base(request))


@router.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    """Dashboard del panel admin (protegido por JS/JWT en el cliente)."""
    return templates.TemplateResponse("admin/dashboard.html", _contexto_base(request))


@router.get("/admin/menu", response_class=HTMLResponse)
def admin_menu(request: Request):
    """Gestión de menú del panel admin."""
    return templates.TemplateResponse("admin/menu_admin.html", _contexto_base(request))


@router.get("/admin/reservas", response_class=HTMLResponse)
def admin_reservas(request: Request):
    """Gestión de reservas del panel admin."""
    return templates.TemplateResponse(
        "admin/reservations_admin.html", _contexto_base(request)
    )
