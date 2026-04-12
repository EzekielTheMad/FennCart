"""Integration tests for /settings/* endpoints.

Tests settings hub page rendering, section switching, LLM save (success/failure),
Ollama config, blank-key preservation, store search/select, preferences save,
and the hot-swap proof. All file-system calls (Fernet key file, Kroger token)
are patched to keep tests fully isolated.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from cryptography.fernet import Fernet
from sqlalchemy import select

from app.models.config_model import AppConfig
from app.services.llm_config import get_active_llm_config
from app.config import Settings


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_TEST_FERNET = Fernet(Fernet.generate_key())


def _mock_settings():
    """Settings instance with test credentials — bypasses SetupGuardMiddleware."""
    settings = MagicMock(spec=Settings)
    settings.kroger_client_id = "test_client_id"
    settings.kroger_client_secret = "test_client_secret"
    settings.llm_api_key = "test_llm_key"
    settings.llm_provider = "anthropic"
    settings.llm_model = "claude-haiku-4-5-20251001"
    settings.session_secret_key = "test_secret"
    settings.base_url = "http://testserver"
    return settings


async def _seed_config(db, **overrides) -> AppConfig:
    """Insert a complete AppConfig row for integration tests."""
    defaults = dict(
        id=1,
        wizard_step="complete",
        wizard_complete=True,
        llm_provider="anthropic",
        llm_model="claude-haiku-4-5-20251001",
        llm_api_key_encrypted=None,
        llm_ollama_base_url=None,
        review_mode="exceptions",
    )
    defaults.update(overrides)
    cfg = AppConfig(**defaults)
    db.add(cfg)
    await db.commit()
    return cfg


def _fernet_patch():
    """Context manager that patches get_or_create_fernet everywhere it is imported."""
    return patch("app.services.oauth_manager.get_or_create_fernet", return_value=_TEST_FERNET)


def _fernet_patch_settings():
    """Patch in the settings router module as well."""
    return patch("app.routers.settings.get_or_create_fernet", return_value=_TEST_FERNET)


def _fernet_patch_llm_config():
    """Patch in llm_config module."""
    return patch("app.services.llm_config.get_or_create_fernet", return_value=_TEST_FERNET)


# ---------------------------------------------------------------------------
# Test 1 — Settings page renders with all section labels
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_settings_page_renders(client, test_db):
    """GET /settings returns 200 with all four sub-nav labels."""
    await _seed_config(test_db)
    with patch("app.main.get_settings", return_value=_mock_settings()):
        with patch("app.routers.settings.get_valid_access_token", new_callable=AsyncMock, return_value=None):
            with _fernet_patch_llm_config():
                response = await client.get("/settings")

    assert response.status_code == 200
    body = response.text
    assert "LLM Provider" in body
    assert "Store" in body
    assert "Kroger Account" in body or "Kroger account" in body
    assert "Preferences" in body
    assert 'id="settings-content"' in body


# ---------------------------------------------------------------------------
# Test 2 — LLM section partial
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_settings_section_llm(client, test_db):
    """GET /settings/section/llm returns LLM form."""
    await _seed_config(test_db)
    with patch("app.main.get_settings", return_value=_mock_settings()):
        with _fernet_patch_llm_config():
            response = await client.get("/settings/section/llm")

    assert response.status_code == 200
    body = response.text
    assert "LLM Provider" in body
    assert "Test connection and save" in body
    assert 'name="provider"' in body


# ---------------------------------------------------------------------------
# Test 3 — Store section partial
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_settings_section_store(client, test_db):
    """GET /settings/section/store returns store search form."""
    await _seed_config(test_db)
    with patch("app.main.get_settings", return_value=_mock_settings()):
        response = await client.get("/settings/section/store")

    assert response.status_code == 200
    body = response.text
    assert "Store location" in body
    assert "Find stores" in body or "zip_code" in body


# ---------------------------------------------------------------------------
# Test 4 — Account section partial
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_settings_section_account(client, test_db):
    """GET /settings/section/account returns Kroger account section."""
    await _seed_config(test_db)
    with patch("app.main.get_settings", return_value=_mock_settings()):
        with patch("app.routers.settings.get_valid_access_token", new_callable=AsyncMock, return_value=None):
            response = await client.get("/settings/section/account")

    assert response.status_code == 200
    body = response.text
    assert "Kroger account" in body
    assert "Re-authorize with Kroger" in body


# ---------------------------------------------------------------------------
# Test 5 — Preferences section partial
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_settings_section_preferences(client, test_db):
    """GET /settings/section/preferences returns preferences form."""
    await _seed_config(test_db)
    with patch("app.main.get_settings", return_value=_mock_settings()):
        response = await client.get("/settings/section/preferences")

    assert response.status_code == 200
    body = response.text
    assert "Preferences" in body
    assert "Save preferences" in body
    assert 'name="review_mode"' in body


# ---------------------------------------------------------------------------
# Test 6 — Save LLM settings (success path)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_save_llm_settings(client, test_db):
    """POST /settings/save-llm with valid key: saves provider/model/key, returns success."""
    await _seed_config(test_db)

    with patch("app.main.get_settings", return_value=_mock_settings()):
        with patch("app.routers.settings.llm_service") as mock_svc:
            mock_svc.test_connection = AsyncMock(return_value=(True, "Connected"))
            with _fernet_patch_settings():
                with _fernet_patch_llm_config():
                    response = await client.post(
                        "/settings/save-llm",
                        data={
                            "provider": "openai",
                            "model": "gpt-4o",
                            "api_key": "sk-test123",
                            "custom_model": "",
                            "ollama_base_url": "",
                        },
                    )

    assert response.status_code == 200
    assert "Provider updated successfully." in response.text

    result = await test_db.execute(select(AppConfig).where(AppConfig.id == 1))
    cfg = result.scalar_one()
    assert cfg.llm_provider == "openai"
    assert cfg.llm_model == "gpt-4o"
    assert cfg.llm_api_key_encrypted is not None


# ---------------------------------------------------------------------------
# Test 7 — Save LLM with invalid key: error returned, DB unchanged
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_save_llm_invalid_key(client, test_db):
    """POST /settings/save-llm with bad key: error partial returned, DB not mutated."""
    await _seed_config(test_db)

    with patch("app.main.get_settings", return_value=_mock_settings()):
        with patch("app.routers.settings.llm_service") as mock_svc:
            mock_svc.test_connection = AsyncMock(return_value=(False, "Invalid API key"))
            with _fernet_patch_llm_config():
                response = await client.post(
                    "/settings/save-llm",
                    data={
                        "provider": "openai",
                        "model": "gpt-4o",
                        "api_key": "sk-bad",
                        "custom_model": "",
                        "ollama_base_url": "",
                    },
                )

    assert response.status_code == 200
    assert "Invalid API key" in response.text

    result = await test_db.execute(select(AppConfig).where(AppConfig.id == 1))
    cfg = result.scalar_one()
    # Provider should still be the original "anthropic"
    assert cfg.llm_provider == "anthropic"


# ---------------------------------------------------------------------------
# Test 8 — Ollama config saved correctly
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_ollama_config(client, test_db):
    """POST /settings/save-llm with Ollama: stores base_url, clears api_key."""
    await _seed_config(test_db)

    with patch("app.main.get_settings", return_value=_mock_settings()):
        with patch("app.routers.settings.llm_service") as mock_svc:
            mock_svc.test_connection = AsyncMock(return_value=(True, "Connected"))
            with _fernet_patch_settings():
                with _fernet_patch_llm_config():
                    response = await client.post(
                        "/settings/save-llm",
                        data={
                            "provider": "ollama",
                            "model": "",
                            "api_key": "",
                            "custom_model": "llama3",
                            "ollama_base_url": "http://localhost:11434",
                        },
                    )

    assert response.status_code == 200
    assert "Provider updated successfully." in response.text

    result = await test_db.execute(select(AppConfig).where(AppConfig.id == 1))
    cfg = result.scalar_one()
    assert cfg.llm_provider == "ollama"
    assert cfg.llm_model == "llama3"
    assert cfg.llm_api_key_encrypted is None
    assert cfg.llm_ollama_base_url == "http://localhost:11434"


# ---------------------------------------------------------------------------
# Test 9 — Blank api_key preserves existing encrypted key
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_save_llm_blank_key_keeps_existing(client, test_db):
    """Empty api_key field leaves llm_api_key_encrypted unchanged."""
    existing_encrypted = _TEST_FERNET.encrypt(b"sk-existing-key").decode()
    await _seed_config(
        test_db,
        llm_provider="openai",
        llm_model="gpt-4o",
        llm_api_key_encrypted=existing_encrypted,
    )

    with patch("app.main.get_settings", return_value=_mock_settings()):
        with patch("app.routers.settings.llm_service") as mock_svc:
            mock_svc.test_connection = AsyncMock(return_value=(True, "Connected"))
            with _fernet_patch_settings():
                with _fernet_patch_llm_config():
                    response = await client.post(
                        "/settings/save-llm",
                        data={
                            "provider": "openai",
                            "model": "gpt-4o-mini",
                            "api_key": "",          # blank — should preserve existing key
                            "custom_model": "",
                            "ollama_base_url": "",
                        },
                    )

    assert response.status_code == 200

    result = await test_db.execute(select(AppConfig).where(AppConfig.id == 1))
    cfg = result.scalar_one()
    # The existing encrypted key must not be overwritten
    assert cfg.llm_api_key_encrypted == existing_encrypted
    assert cfg.llm_model == "gpt-4o-mini"


# ---------------------------------------------------------------------------
# Test 10 — Store search returns store list
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_search_stores(client, test_db):
    """POST /settings/search-stores returns store results."""
    await _seed_config(test_db)

    fake_stores = [
        {
            "locationId": "123",
            "name": "Fry's #123",
            "address": {
                "addressLine1": "123 Main St",
                "city": "Phoenix",
                "state": "AZ",
                "zipCode": "85001",
            },
        }
    ]

    with patch("app.main.get_settings", return_value=_mock_settings()):
        with patch("app.routers.settings.kroger_client") as mock_kc:
            mock_kc.get_app_token = AsyncMock(return_value=(True, "ok", "fake-token"))
            mock_kc.search_stores_by_zip = AsyncMock(return_value=(True, "ok", fake_stores))
            response = await client.post(
                "/settings/search-stores",
                data={"zip_code": "85001"},
            )

    assert response.status_code == 200
    assert "Fry&#39;s #123" in response.text or "Fry's #123" in response.text


# ---------------------------------------------------------------------------
# Test 11 — Select store persists correctly, wizard_step unchanged
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_select_store(client, test_db):
    """POST /settings/select-store saves store without touching wizard_step."""
    await _seed_config(test_db)

    with patch("app.main.get_settings", return_value=_mock_settings()):
        response = await client.post(
            "/settings/select-store",
            data={
                "store_id": "123",
                "store_name": "Fry's #123",
                "store_zip": "85001",
            },
        )

    assert response.status_code == 200
    assert "saved" in response.text.lower()

    result = await test_db.execute(select(AppConfig).where(AppConfig.id == 1))
    cfg = result.scalar_one()
    assert cfg.store_id == "123"
    assert cfg.store_name == "Fry's #123"
    # wizard_step must remain unchanged (not mutated by settings store selection)
    assert cfg.wizard_step == "complete"


# ---------------------------------------------------------------------------
# Test 12 — Save preferences persists review_mode
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_save_preferences(client, test_db):
    """POST /settings/save-preferences persists review_mode='full'."""
    await _seed_config(test_db)

    with patch("app.main.get_settings", return_value=_mock_settings()):
        response = await client.post(
            "/settings/save-preferences",
            data={"review_mode": "full"},
        )

    assert response.status_code == 200
    assert "Preferences saved" in response.text

    result = await test_db.execute(select(AppConfig).where(AppConfig.id == 1))
    cfg = result.scalar_one()
    assert cfg.review_mode == "full"


# ---------------------------------------------------------------------------
# Test 13 — Hot-swap: save LLM -> next get_active_llm_config picks up new value
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_llm_hotswap(client, test_db, test_settings):
    """Saving new LLM provider via endpoint -> get_active_llm_config returns new provider."""
    await _seed_config(test_db, llm_provider="anthropic")

    with patch("app.main.get_settings", return_value=_mock_settings()):
        with patch("app.routers.settings.llm_service") as mock_svc:
            mock_svc.test_connection = AsyncMock(return_value=(True, "Connected"))
            with _fernet_patch_settings():
                with _fernet_patch_llm_config():
                    response = await client.post(
                        "/settings/save-llm",
                        data={
                            "provider": "openai",
                            "model": "gpt-4o",
                            "api_key": "sk-new-key",
                            "custom_model": "",
                            "ollama_base_url": "",
                        },
                    )

    assert response.status_code == 200
    assert "Provider updated successfully." in response.text

    # Hot-swap proof: next call to get_active_llm_config sees the new value
    with patch("app.services.llm_config.get_settings", return_value=test_settings):
        with _fernet_patch_llm_config():
            llm_cfg = await get_active_llm_config(test_db)

    assert llm_cfg["provider"] == "openai"
