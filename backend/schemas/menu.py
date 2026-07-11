"""Schemas Pydantic para el menú (categorías y platos)."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Categorías
# ---------------------------------------------------------------------------
class MenuCategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    order_index: int = 0
    is_active: bool = True


class MenuCategoryCreate(MenuCategoryBase):
    pass


class MenuCategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    order_index: Optional[int] = None
    is_active: Optional[bool] = None


class MenuCategoryResponse(MenuCategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Platos
# ---------------------------------------------------------------------------
class MenuItemBase(BaseModel):
    category_id: int
    name: str
    description: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    is_available: bool = True
    is_featured: bool = False
    order_index: int = 0


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None
    is_featured: Optional[bool] = None
    order_index: Optional[int] = None


class MenuItemResponse(MenuItemBase):
    id: int
    created_at: datetime
    category_slug: Optional[str] = None
    category_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MenuCategoryWithItems(MenuCategoryResponse):
    items: List[MenuItemResponse] = []
