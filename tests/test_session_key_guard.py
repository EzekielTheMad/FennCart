"""Tests for SESSION_SECRET_KEY missing guard (ERR-01)."""
import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport


@pytest.mark.anyio
async def test_missing_session_key_shows_error_page():
    """When SESSION_KEY_MISSING is True, all non-exempt routes serve session_error.html."""
    # Patch SESSION_KEY_MISSING at module level before making request
    with patch("app.main.SESSION_KEY_MISSING", True):
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")
            assert response.status_code == 500
            assert "SESSION_SECRET_KEY not set" in response.text
            assert "secrets.token_urlsafe" in response.text


@pytest.mark.anyio
async def test_missing_session_key_allows_static():
    """Static files should still be served even when session key is missing."""
    with patch("app.main.SESSION_KEY_MISSING", True):
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            # /health is exempt
            assert response.status_code == 200


@pytest.mark.anyio
async def test_valid_session_key_does_not_show_error():
    """When SESSION_KEY_MISSING is False, the error page is not served.

    Must also patch get_settings to provide Kroger credentials so the
    middleware doesn't block on missing config, and get_session to avoid
    hitting the production DB path.
    """
    from unittest.mock import AsyncMock, MagicMock

    # Create a mock session that returns a cfg with wizard_complete=True
    mock_cfg = MagicMock()
    mock_cfg.wizard_complete = True
    mock_cfg.kroger_client_id_encrypted = None
    mock_cfg.kroger_client_secret_encrypted = None

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_cfg

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def fake_get_session():
        yield mock_session

    with patch("app.main.SESSION_KEY_MISSING", False), \
         patch("app.main.get_settings") as mock_settings, \
         patch("app.main.get_session", fake_get_session):
        mock_settings.return_value.kroger_client_id = "test-id"
        mock_settings.return_value.kroger_client_secret = "test-secret"
        mock_settings.return_value.session_secret_key = "test-key"
        from app.main import app
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/")
            # Should NOT contain the session error page content
            assert "SESSION_SECRET_KEY not set" not in response.text
