"""Unit tests for get_active_llm_config().

Tests DB-first reads, Fernet decrypt, env fallback, and Ollama config paths.
All tests use the in-memory test_db fixture and patch get_or_create_fernet
to avoid file-system access to /data/app.key.
"""
import pytest
from unittest.mock import patch
from cryptography.fernet import Fernet

from app.models.config_model import AppConfig
from app.services.llm_config import get_active_llm_config


# ---------------------------------------------------------------------------
# Test 1 — env fallback when no AppConfig row exists
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_llm_config_env_fallback(test_db, test_settings):
    """No AppConfig row in DB: returns Settings env values."""
    with patch("app.services.llm_config.get_settings", return_value=test_settings):
        cfg = await get_active_llm_config(test_db)

    assert cfg["provider"] == "anthropic"
    assert cfg["model"] == "claude-3-haiku-20240307"
    assert cfg["api_key"] == "test_llm_key"
    assert cfg["ollama_base_url"] is None


# ---------------------------------------------------------------------------
# Test 2 — DB row present, no encrypted key -> env key fallback
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_llm_config_from_db(test_db, test_settings):
    """AppConfig row with llm_provider/model but no encrypted key returns env key."""
    row = AppConfig(
        id=1,
        wizard_step="complete",
        wizard_complete=True,
        llm_provider="openai",
        llm_model="gpt-4o",
        llm_api_key_encrypted=None,
    )
    test_db.add(row)
    await test_db.commit()

    with patch("app.services.llm_config.get_settings", return_value=test_settings):
        cfg = await get_active_llm_config(test_db)

    assert cfg["provider"] == "openai"
    assert cfg["model"] == "gpt-4o"
    # No encrypted key -> falls back to env var
    assert cfg["api_key"] == "test_llm_key"
    assert cfg["ollama_base_url"] is None


# ---------------------------------------------------------------------------
# Test 3 — Fernet-encrypted key is decrypted correctly
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_llm_config_encrypted_key(test_db, test_settings):
    """Encrypted key stored in DB is Fernet-decrypted and returned."""
    test_fernet = Fernet(Fernet.generate_key())
    encrypted = test_fernet.encrypt(b"sk-real-key").decode()

    row = AppConfig(
        id=1,
        wizard_step="complete",
        wizard_complete=True,
        llm_provider="openai",
        llm_model="gpt-4o",
        llm_api_key_encrypted=encrypted,
    )
    test_db.add(row)
    await test_db.commit()

    with patch("app.services.llm_config.get_settings", return_value=test_settings):
        with patch("app.services.llm_config.get_or_create_fernet", return_value=test_fernet):
            cfg = await get_active_llm_config(test_db)

    assert cfg["api_key"] == "sk-real-key"
    assert cfg["provider"] == "openai"


# ---------------------------------------------------------------------------
# Test 4 — Ollama provider: returns base_url, env api_key (unused by Ollama)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_llm_config_ollama(test_db, test_settings):
    """Ollama config row returns ollama_base_url and env api_key fallback."""
    row = AppConfig(
        id=1,
        wizard_step="complete",
        wizard_complete=True,
        llm_provider="ollama",
        llm_model="llama3",
        llm_api_key_encrypted=None,
        llm_ollama_base_url="http://localhost:11434",
    )
    test_db.add(row)
    await test_db.commit()

    with patch("app.services.llm_config.get_settings", return_value=test_settings):
        cfg = await get_active_llm_config(test_db)

    assert cfg["provider"] == "ollama"
    assert cfg["model"] == "llama3"
    assert cfg["ollama_base_url"] == "http://localhost:11434"
    # api_key is env fallback (Ollama ignores it but it should be the env value)
    assert cfg["api_key"] == "test_llm_key"
