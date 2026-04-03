"""Tests for the setup wizard flow."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.models.config_model import AppConfig
from app.config import Settings


def _mock_settings_with_creds():
    """Return a Settings instance with Kroger credentials populated (bypasses missing_config check)."""
    settings = MagicMock(spec=Settings)
    settings.kroger_client_id = "test_client_id"
    settings.kroger_client_secret = "test_client_secret"
    settings.llm_api_key = "test_llm_key"
    settings.llm_provider = "anthropic"
    settings.llm_model = "claude-3-haiku-20240307"
    settings.session_secret_key = "test_secret"
    settings.base_url = "http://localhost:8000"
    return settings


@pytest.mark.anyio
async def test_wizard_redirects_when_incomplete(client, test_db):
    """GET / should redirect to /setup when wizard is not complete."""
    # Create incomplete AppConfig
    test_db.add(AppConfig(id=1, wizard_step="start", wizard_complete=False))
    await test_db.commit()
    # Patch settings so middleware sees credentials and reaches wizard check
    with patch("app.main.get_settings", return_value=_mock_settings_with_creds()):
        response = await client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/setup" in response.headers.get("location", "")


@pytest.mark.anyio
async def test_wizard_setup_page_renders(client):
    """GET /setup should return 200 with wizard content."""
    response = await client.get("/setup")
    assert response.status_code == 200
    assert "Connect your LLM provider" in response.text or "wizard" in response.text.lower()


@pytest.mark.anyio
@patch("app.routers.setup.llm_service")
async def test_validate_llm_success(mock_llm, client, test_db):
    """POST /setup/validate-llm should advance to step 2 on success."""
    mock_llm.test_connection = AsyncMock(return_value=(True, "Connected"))
    response = await client.post("/setup/validate-llm")
    assert response.status_code == 200
    assert "Kroger" in response.text  # Should show step 2 content


@pytest.mark.anyio
async def test_wizard_resumable(client, test_db):
    """Wizard should resume from last completed step (D-02)."""
    test_db.add(AppConfig(id=1, wizard_step="kroger", wizard_complete=False))
    await test_db.commit()
    response = await client.get("/setup")
    assert response.status_code == 200
    # Should show store step (step after kroger), not LLM step
