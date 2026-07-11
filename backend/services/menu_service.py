"""Lógica de negocio del menú."""
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.models.menu import MenuCategory, MenuItem
from backend.schemas.menu import (
    MenuCategoryCreate,
    MenuItemCreate,
    MenuItemUpdate,
)


def get_categories(db: Session, only_active: bool = True) -> List[MenuCategory]:
    """Devuelve las categorías ordenadas por order_index."""
    query = db.query(MenuCategory)
    if only_active:
        query = query.filter(MenuCategory.is_active.is_(True))
    return query.order_by(MenuCategory.order_index).all()


def create_category(db: Session, data: MenuCategoryCreate) -> MenuCategory:
    category = MenuCategory(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def get_items(
    db: Session,
    category_slug: Optional[str] = None,
    featured: Optional[bool] = None,
    search: Optional[str] = None,
) -> List[MenuItem]:
    """Devuelve los platos aplicando los filtros indicados."""
    query = db.query(MenuItem).join(MenuCategory)

    if category_slug:
        query = query.filter(MenuCategory.slug == category_slug)
    if featured is not None:
        query = query.filter(MenuItem.is_featured.is_(featured))
    if search:
        patron = f"%{search.lower()}%"
        query = query.filter(
            (MenuItem.name.ilike(patron)) | (MenuItem.description.ilike(patron))
        )

    return query.order_by(MenuCategory.order_index, MenuItem.order_index).all()


def get_item(db: Session, item_id: int) -> Optional[MenuItem]:
    return db.query(MenuItem).filter(MenuItem.id == item_id).first()


def create_item(db: Session, data: MenuItemCreate) -> MenuItem:
    item = MenuItem(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, item_id: int, data: MenuItemUpdate) -> Optional[MenuItem]:
    item = get_item(db, item_id)
    if not item:
        return None
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(item, campo, valor)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item_id: int) -> bool:
    item = get_item(db, item_id)
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True


def serialize_item(item: MenuItem) -> dict:
    """Convierte un plato en diccionario incluyendo datos de la categoría."""
    return {
        "id": item.id,
        "category_id": item.category_id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "image_url": item.image_url,
        "is_available": item.is_available,
        "is_featured": item.is_featured,
        "order_index": item.order_index,
        "created_at": item.created_at,
        "category_slug": item.category.slug if item.category else None,
        "category_name": item.category.name if item.category else None,
    }
