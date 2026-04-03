from sqlmodel import SQLModel, Field
from typing import Optional


class AppConfig(SQLModel, table=True):
    __tablename__ = "app_config"
    id: int = Field(default=1, primary_key=True)
    wizard_step: str = Field(default="start")
    wizard_complete: bool = Field(default=False)
    store_id: Optional[str] = None
    store_name: Optional[str] = None
    store_zip: Optional[str] = None
    llm_provider: str = Field(default="anthropic")
    llm_model: str = Field(default="claude-3-haiku-20240307")
