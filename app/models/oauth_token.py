from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class OAuthToken(SQLModel, table=True):
    __tablename__ = "oauth_tokens"
    id: int = Field(default=1, primary_key=True)
    access_token_encrypted: str = Field(default="")
    refresh_token_encrypted: str = Field(default="")
    expires_at: Optional[datetime] = None
    scope: Optional[str] = None
    token_type: str = Field(default="Bearer")
