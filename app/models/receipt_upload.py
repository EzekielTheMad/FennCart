from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class ReceiptUpload(SQLModel, table=True):
    __tablename__ = "receipt_uploads"

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    items_extracted: int = Field(default=0)
    items_confirmed: int = Field(default=0)
    parse_status: str = Field(default="pending")  # "pending","parsed","confirmed","failed"
    parse_warnings: Optional[str] = None          # JSON list of warning strings
    parsed_items_json: Optional[str] = None       # JSON list of parsed receipt items
    contradictions_json: Optional[str] = None     # JSON list of contradiction candidates
