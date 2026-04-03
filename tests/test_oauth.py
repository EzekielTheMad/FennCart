import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from app.services.oauth_manager import store_token, get_decrypted_token, get_valid_access_token, get_or_create_fernet
from app.models.oauth_token import OAuthToken
from app.models.config_model import AppConfig
import tempfile
from pathlib import Path


@pytest.fixture
def temp_key_path(tmp_path):
    """Temporary Fernet key path for tests."""
    key_file = tmp_path / "app.key"
    return key_file


@pytest.mark.anyio
async def test_store_token_encrypts(test_db, temp_key_path):
    """Tokens stored in DB should be Fernet-encrypted, not plaintext (D-06)."""
    with patch("app.services.oauth_manager.KEY_PATH", temp_key_path):
        token = {
            "access_token": "kroger_access_abc123",
            "refresh_token": "kroger_refresh_xyz789",
            "expires_in": 1800,
        }
        await store_token(token, test_db)

        from sqlalchemy import select
        result = await test_db.execute(select(OAuthToken).where(OAuthToken.id == 1))
        record = result.scalar_one()

        # Encrypted values must NOT contain the plaintext
        assert "kroger_access_abc123" not in record.access_token_encrypted
        assert "kroger_refresh_xyz789" not in record.refresh_token_encrypted
        # But decryption should recover them
        f = get_or_create_fernet()
        assert f.decrypt(record.access_token_encrypted.encode()).decode() == "kroger_access_abc123"


@pytest.mark.anyio
async def test_get_decrypted_token(test_db, temp_key_path):
    """Decrypted token should match original plaintext."""
    with patch("app.services.oauth_manager.KEY_PATH", temp_key_path):
        token = {"access_token": "abc", "refresh_token": "xyz", "expires_in": 1800}
        await store_token(token, test_db)
        result = await get_decrypted_token(test_db)
        assert result["access_token"] == "abc"
        assert result["refresh_token"] == "xyz"


@pytest.mark.anyio
async def test_proactive_refresh_within_60s(test_db, temp_key_path):
    """Token within 60s of expiry triggers refresh (SETUP-04)."""
    with patch("app.services.oauth_manager.KEY_PATH", temp_key_path):
        # Store a token that expires in 30 seconds (within the 60s margin)
        f = get_or_create_fernet()
        record = OAuthToken(
            id=1,
            access_token_encrypted=f.encrypt(b"old_token").decode(),
            refresh_token_encrypted=f.encrypt(b"refresh_token").decode(),
            expires_at=datetime.utcnow() + timedelta(seconds=30),
        )
        test_db.add(record)
        await test_db.commit()

        # Mock the refresh call
        new_token = {"access_token": "new_token", "refresh_token": "new_refresh", "expires_in": 1800}
        with patch("app.services.oauth_manager._refresh_token", new_callable=AsyncMock, return_value=new_token):
            result = await get_valid_access_token(test_db)
            assert result == "new_token"


@pytest.mark.anyio
async def test_no_refresh_when_token_fresh(test_db, temp_key_path):
    """Token with plenty of time remaining should not trigger refresh."""
    with patch("app.services.oauth_manager.KEY_PATH", temp_key_path):
        f = get_or_create_fernet()
        record = OAuthToken(
            id=1,
            access_token_encrypted=f.encrypt(b"fresh_token").decode(),
            refresh_token_encrypted=f.encrypt(b"refresh_token").decode(),
            expires_at=datetime.utcnow() + timedelta(seconds=600),
        )
        test_db.add(record)
        await test_db.commit()

        with patch("app.services.oauth_manager._refresh_token", new_callable=AsyncMock) as mock_refresh:
            result = await get_valid_access_token(test_db)
            assert result == "fresh_token"
            mock_refresh.assert_not_called()


@pytest.mark.anyio
async def test_auth_callback_marks_wizard_complete(client, test_db):
    """OAuth callback should set wizard_complete = True and wizard_step = 'complete'."""
    # Pre-create AppConfig at store step
    test_db.add(AppConfig(id=1, wizard_step="store", wizard_complete=False))
    await test_db.commit()

    # Mock Authlib's authorize_access_token
    mock_token = {"access_token": "tok", "refresh_token": "ref", "expires_in": 1800, "scope": "openid"}
    with patch("app.routers.auth.oauth") as mock_oauth, \
         patch("app.routers.auth.store_token", new_callable=AsyncMock):
        mock_oauth.kroger.authorize_access_token = AsyncMock(return_value=mock_token)
        response = await client.get("/auth/kroger/callback", follow_redirects=False)
        # Should redirect to /tour
        assert response.status_code == 302
        assert "/tour" in response.headers.get("location", "")
