from authlib.integrations.starlette_client import OAuth
from cryptography.fernet import Fernet
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.config import get_settings
from app.models.oauth_token import OAuthToken

# Fernet key management (D-06)
KEY_PATH = Path("/data/app.key")


def get_or_create_fernet() -> Fernet:
    """Load or generate Fernet key from Docker volume."""
    if KEY_PATH.exists():
        return Fernet(KEY_PATH.read_bytes().strip())
    key = Fernet.generate_key()
    KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    KEY_PATH.write_bytes(key)
    return Fernet(key)


# Authlib OAuth client setup
oauth = OAuth()


def register_kroger_oauth():
    """Register the Kroger OAuth provider. Call at app startup."""
    settings = get_settings()
    oauth.register(
        name="kroger",
        client_id=settings.kroger_client_id,
        client_secret=settings.kroger_client_secret,
        authorize_url="https://api.kroger.com/v1/connect/oauth2/authorize",
        access_token_url="https://api.kroger.com/v1/connect/oauth2/token",
        client_kwargs={"scope": "openid profile cart.basic:write product.compact"},
    )


# Token storage with encryption
async def store_token(token: dict, db: AsyncSession) -> None:
    """Encrypt and store OAuth tokens in SQLite (D-06)."""
    f = get_or_create_fernet()
    access_enc = f.encrypt(token["access_token"].encode()).decode()
    refresh_enc = f.encrypt(token["refresh_token"].encode()).decode()
    expires_at = datetime.utcnow() + timedelta(seconds=token.get("expires_in", 1800))

    result = await db.execute(select(OAuthToken).where(OAuthToken.id == 1))
    existing = result.scalar_one_or_none()

    if existing:
        existing.access_token_encrypted = access_enc
        existing.refresh_token_encrypted = refresh_enc
        existing.expires_at = expires_at
        existing.scope = token.get("scope", "")
    else:
        record = OAuthToken(
            id=1,
            access_token_encrypted=access_enc,
            refresh_token_encrypted=refresh_enc,
            expires_at=expires_at,
            scope=token.get("scope", ""),
        )
        db.add(record)
    await db.commit()


async def get_decrypted_token(db: AsyncSession) -> Optional[dict]:
    """Read and decrypt stored OAuth token."""
    result = await db.execute(select(OAuthToken).where(OAuthToken.id == 1))
    record = result.scalar_one_or_none()
    if not record or not record.access_token_encrypted:
        return None
    f = get_or_create_fernet()
    return {
        "access_token": f.decrypt(record.access_token_encrypted.encode()).decode(),
        "refresh_token": f.decrypt(record.refresh_token_encrypted.encode()).decode(),
        "expires_at": record.expires_at,
    }


async def _refresh_token(refresh_token: str) -> dict:
    """Exchange refresh token for new access token at Kroger."""
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.kroger.com/v1/connect/oauth2/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            auth=(settings.kroger_client_id, settings.kroger_client_secret),
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()


async def get_valid_access_token(db: AsyncSession) -> Optional[str]:
    """Get a valid access token, refreshing proactively if within 60s of expiry (SETUP-04).

    Returns the decrypted access token string, or None if no token is stored.
    Performs proactive refresh when token expires within 60 seconds.
    """
    token_data = await get_decrypted_token(db)
    if not token_data:
        return None

    # Proactive refresh: if within 60 seconds of expiry
    if token_data["expires_at"] and (token_data["expires_at"] - datetime.utcnow()) < timedelta(seconds=60):
        try:
            new_token = await _refresh_token(token_data["refresh_token"])
            await store_token(new_token, db)
            return new_token["access_token"]
        except Exception:
            # Refresh failed — return existing token (may be expired, caller handles 401)
            return token_data["access_token"]

    return token_data["access_token"]
