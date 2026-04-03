from pydantic import BaseModel, Field
from typing import Optional


class ParsedListItem(BaseModel):
    """A structured item parsed from raw shopping list text."""
    name: str
    quantity: int = Field(default=1)
    unit: Optional[str] = None
    notes: Optional[str] = None


class ProductCandidate(BaseModel):
    """A Kroger product candidate for matching."""
    upc: str
    description: str
    brand: str
    size: str
    price_regular: Optional[float] = None
    price_promo: Optional[float] = None
    thumbnail_url: Optional[str] = None


class ItemMatch(BaseModel):
    """LLM match decision for one shopping list item."""
    list_item: str
    selected_upc: str
    selected_description: str
    selected_brand: str = ""
    selected_size: str = ""
    selected_price: Optional[float] = None
    selected_thumbnail: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    alternatives: list[str] = Field(default_factory=list)


class MatchResult(BaseModel):
    """Complete match result for all items in a shopping list."""
    matches: list[ItemMatch]


class ConfirmedItem(BaseModel):
    """A user-confirmed item ready for cart add."""
    upc: str
    description: str
    brand: str = ""
    size: str = ""
    quantity: int = 1
    price_regular: Optional[float] = None
    price_promo: Optional[float] = None
