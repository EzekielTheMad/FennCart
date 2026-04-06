from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint


class PreferenceEntry(SQLModel, table=True):
    __tablename__ = "preference_entries"
    __table_args__ = (
        UniqueConstraint("product_category", "brand", "product_name", name="uq_pref_category_brand_product"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    product_category: str = Field(index=True)   # "milk", "cheddar cheese", "pasta"
    brand: str                                    # "Tillamook", "Kroger", ""
    product_name: str                             # "Medium Cheddar", "2% Milk"
    purchase_count: int = Field(default=1)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(default="manual")         # "receipt", "nl_chat", "manual"
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
