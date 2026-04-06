from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class CartItem(SQLModel, table=True):
    __tablename__ = "cart_items"
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="cart_sessions.id")
    upc: str
    description: str
    brand: Optional[str] = None
    size: Optional[str] = None
    quantity: int = Field(default=1)
    price_regular: Optional[float] = None
    price_promo: Optional[float] = None
    added_at: datetime = Field(default_factory=datetime.utcnow)
