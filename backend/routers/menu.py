"""Router del menú (público + gestión admin)."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.auth.jwt_handler import get_current_admin
from backend.database import get_db
from backend.models.user import User
from backend.schemas.menu import (
    MenuCategoryCreate,
    MenuCategoryResponse,
    MenuItemCreate,
    MenuItemResponse,
    MenuItemUpdate,
)
from backend.services import menu_service

router = APIRouter(prefix="/api/menu", tags=["Menú"])


# ---------------------------------------------------------------------------
# Categorías
# ---------------------------------------------------------------------------
@router.get("/categories", response_model=List[MenuCategoryResponse])
def listar_categorias(db: Session = Depends(get_db)):
    """Lista todas las categorías activas del menú."""
    return menu_service.get_categories(db)


@router.post(
    "/categories",
    response_model=MenuCategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_categoria(
    datos: MenuCategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Crea una nueva categoría (solo admin)."""
    return menu_service.create_category(db, datos)


# ---------------------------------------------------------------------------
# Platos
# ---------------------------------------------------------------------------
@router.get("/items", response_model=List[MenuItemResponse])
def listar_platos(
    category_slug: Optional[str] = Query(None),
    featured: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Lista los platos aplicando filtros opcionales."""
    items = menu_service.get_items(db, category_slug, featured, search)
    return [menu_service.serialize_item(i) for i in items]


@router.get("/items/{item_id}", response_model=MenuItemResponse)
def obtener_plato(item_id: int, db: Session = Depends(get_db)):
    """Devuelve un plato concreto por su id."""
    item = menu_service.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Plato no encontrado")
    return menu_service.serialize_item(item)


@router.post(
    "/items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED
)
def crear_plato(
    datos: MenuItemCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Crea un nuevo plato (solo admin)."""
    item = menu_service.create_item(db, datos)
    return menu_service.serialize_item(item)


@router.put("/items/{item_id}", response_model=MenuItemResponse)
def actualizar_plato(
    item_id: int,
    datos: MenuItemUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Actualiza un plato existente (solo admin)."""
    item = menu_service.update_item(db, item_id, datos)
    if not item:
        raise HTTPException(status_code=404, detail="Plato no encontrado")
    return menu_service.serialize_item(item)


@router.delete("/items/{item_id}", status_code=status.HTTP_200_OK)
def eliminar_plato(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Elimina un plato (solo admin)."""
    if not menu_service.delete_item(db, item_id):
        raise HTTPException(status_code=404, detail="Plato no encontrado")
    return {"detail": "Plato eliminado correctamente"}
