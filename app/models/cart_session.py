from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class CartSession(SQLModel, table=True):
    __tablename__ = "cart_sessions"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    item_count: int = Field(default=0)
    estimated_total: Optional[float] = None
