"""DB-authoritative Kroger credential reader for hot-swap support.

Reads Kroger client_id and client_secret from AppConfig at request time.
Falls back to env-based Settings when no DB override exists.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.config_model import AppConfig
from app.config import get_settings
from app.services.oauth_manager import get_or_create_fernet


async def get_active_kroger_config(db: AsyncSession) -> dict:
    """Return active Kroger credentials from DB, falling back to env Settings.

    Returns dict with keys: client_id, client_secret.

    Priority:
    1. AppConfig row in DB (written by settings page or wizard, hot-swappable).
    2. env-based Settings (kroger_client_id, kroger_client_secret).

    Encrypted values are Fernet-decrypted using the same key file as OAuth tokens.
    Falls back to env var if decryption fails.
    """
    result = await db.execute(select(AppConfig).where(AppConfig.id == 1))
    cfg = result.scalar_one_or_none()
    settings = get_settings()

    if cfg and cfg.kroger_client_id_encrypted:
        client_id = settings.kroger_client_id  # env fallback
        client_secret = settings.kroger_client_secret

        try:
            f = get_or_create_fernet()
            client_id = f.decrypt(cfg.kroger_client_id_encrypted.encode()).decode()
        except Exception:
            pass

        if cfg.kroger_client_secret_encrypted:
            try:
                f = get_or_create_fernet()
                client_secret = f.decrypt(cfg.kroger_client_secret_encrypted.encode()).decode()
            except Exception:
                pass

        return {
            "client_id": client_id,
            "client_secret": client_secret,
        }

    return {
        "client_id": settings.kroger_client_id,
        "client_secret": settings.kroger_client_secret,
    }
