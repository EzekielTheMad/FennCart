from sqlmodel import SQLModel, Field
from typing import Optional

from app.constants import DEFAULT_LLM_PROVIDER, DEFAULT_LLM_MODEL


class AppConfig(SQLModel, table=True):
    __tablename__ = "app_config"
    id: int = Field(default=1, primary_key=True)
    wizard_step: str = Field(default="start")
    wizard_complete: bool = Field(default=False)
    store_id: Optional[str] = None
    store_name: Optional[str] = None
    store_zip: Optional[str] = None
    llm_provider: str = Field(default=DEFAULT_LLM_PROVIDER)
    llm_model: str = Field(default=DEFAULT_LLM_MODEL)
    llm_api_key_encrypted: Optional[str] = None
    llm_ollama_base_url: Optional[str] = None
    review_mode: str = Field(default="exceptions")
    kroger_client_id_encrypted: Optional[str] = None
    kroger_client_secret_encrypted: Optional[str] = None
