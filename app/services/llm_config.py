"""DB-authoritative LLM config reader for hot-swap support.

Reads LLM provider/model/api_key from AppConfig at request time.
Falls back to env-based Settings when no DB override exists.
This replaces get_settings() for LLM fields in the shopping router.
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config_model import AppConfig
from app.config import get_settings
from app.services.oauth_manager import get_or_create_fernet


async def get_active_llm_config(db: AsyncSession) -> dict:
    """Return active LLM config from DB, falling back to env Settings.

    Returns dict with keys: provider, model, api_key, ollama_base_url.

    Priority:
    1. AppConfig row in DB (written by settings page, hot-swappable).
    2. env-based Settings (llm_provider, llm_model, llm_api_key).

    When llm_api_key_encrypted is set, the key is Fernet-decrypted using
    the same key file used for OAuth tokens (get_or_create_fernet).
    Falls back to env var if decryption fails.
    """
    result = await db.execute(select(AppConfig).where(AppConfig.id == 1))
    cfg = result.scalar_one_or_none()
    settings = get_settings()

    if cfg and cfg.llm_provider:
        api_key = settings.llm_api_key  # env var default

        if cfg.llm_api_key_encrypted:
            try:
                f = get_or_create_fernet()
                api_key = f.decrypt(cfg.llm_api_key_encrypted.encode()).decode()
            except Exception:
                pass  # Fall back to env var if decryption fails

        return {
            "provider": cfg.llm_provider,
            "model": cfg.llm_model,
            "api_key": api_key,
            "ollama_base_url": cfg.llm_ollama_base_url,
        }

    return {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "api_key": settings.llm_api_key,
        "ollama_base_url": None,
    }
