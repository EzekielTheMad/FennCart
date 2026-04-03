from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    kroger_client_id: str = ""
    kroger_client_secret: str = ""
    llm_api_key: str = ""
    llm_provider: str = "anthropic"
    llm_model: str = "claude-3-haiku-20240307"
    base_url: str = "http://localhost:8000"
    session_secret_key: str = "change-me-in-production"
    port: int = 8000
    database_url: str = "sqlite+aiosqlite:////data/fenncart.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
