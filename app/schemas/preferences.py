"""Pydantic schemas for the preference system: receipt parsing, preference CRUD, NL chat, contradiction detection."""
from typing import Optional
from pydantic import BaseModel, Field


class ReceiptLineItem(BaseModel):
    """Single line item parsed from a receipt PDF."""
    product_name: str
    brand: str = ""
    product_category: str
    quantity: int = 1
    size: str = ""
    price: Optional[float] = None
    confidence: float = Field(ge=0.0, le=1.0)


class ParsedReceipt(BaseModel):
    """Instructor response model for receipt parsing."""
    items: list[ReceiptLineItem]
    parse_warnings: list[str] = Field(default_factory=list)


class ContradictionCandidate(BaseModel):
    """A detected brand contradiction for user resolution (D-06)."""
    category: str
    existing_brand: str
    existing_count: int
    new_brand: str
    product_name: str
    new_item_index: int          # Index into the parsed items list
    resolution: Optional[str] = None  # "new_preference" | "one_time"


class PreferenceDelta(BaseModel):
    """Structured interpretation of a natural language preference update (D-07, D-08)."""
    action: str                  # "replace" | "add" | "remove" | "clarify"
    category: str = ""
    old_brand: Optional[str] = None
    new_brand: Optional[str] = None
    product_name: Optional[str] = None
    clarification_question: Optional[str] = None
    human_summary: str


class PreferenceCreateRequest(BaseModel):
    """Request body for manually adding a preference."""
    product_category: str
    brand: str
    product_name: str
    notes: Optional[str] = None


class PreferenceUpdateRequest(BaseModel):
    """Request body for editing an existing preference."""
    product_name: Optional[str] = None
    brand: Optional[str] = None
    product_category: Optional[str] = None
    notes: Optional[str] = None
