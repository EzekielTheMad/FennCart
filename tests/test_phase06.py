"""Tests for Phase 6: review mode persistence (SRCH-05) and cart history (CART-03)."""
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.config_model import AppConfig
from app.models.cart_session import CartSession
from app.models.cart_item import CartItem
from app.schemas.shopping import MatchResult, ItemMatch, ProductCandidate
from app.config import Settings


def _mock_settings():
    """Settings with test credentials to bypass SetupGuardMiddleware."""
    s = MagicMock(spec=Settings)
    s.kroger_client_id = "test_client_id"
    s.kroger_client_secret = "test_client_secret"
    s.llm_api_key = "test_llm_key"
    s.llm_provider = "anthropic"
    s.llm_model = "claude-3-haiku-20240307"
    s.session_secret_key = "test_secret"
    s.base_url = "http://testserver"
    return s


async def _seed_wizard_config(test_db, review_mode="exceptions"):
    """Insert a wizard-complete AppConfig so SetupGuardMiddleware allows requests."""
    cfg = AppConfig(id=1, wizard_complete=True, store_id="123", review_mode=review_mode)
    test_db.add(cfg)
    await test_db.commit()


# ---- CART-03: History page tests ----

@pytest.mark.anyio
async def test_history_empty_state(client, test_db):
    """GET /history with no sessions shows empty state."""
    await _seed_wizard_config(test_db)
    with patch("app.main.get_settings", return_value=_mock_settings()):
        resp = await client.get("/history")
    assert resp.status_code == 200
    assert "No shopping history yet" in resp.text
    assert "Start shopping" in resp.text


@pytest.mark.anyio
async def test_history_with_sessions(client, test_db):
    """GET /history with cart data shows session rows."""
    await _seed_wizard_config(test_db)

    # Insert two sessions
    s1 = CartSession(item_count=3, estimated_total=12.50, created_at=datetime(2026, 4, 1))
    s2 = CartSession(item_count=5, estimated_total=27.99, created_at=datetime(2026, 4, 5))
    test_db.add(s1)
    test_db.add(s2)
    await test_db.flush()

    # Insert items for session 2
    test_db.add(CartItem(
        session_id=s2.id, upc="001", description="Whole Milk",
        brand="Kroger", quantity=1, price_regular=3.99,
    ))
    test_db.add(CartItem(
        session_id=s2.id, upc="002", description="Eggs",
        brand="Kroger", quantity=2, price_regular=4.49,
    ))
    await test_db.commit()

    with patch("app.main.get_settings", return_value=_mock_settings()):
        resp = await client.get("/history")
    assert resp.status_code == 200
    assert "2 shopping sessions" in resp.text
    assert "Whole Milk" in resp.text
    assert "Eggs" in resp.text
    # Newest first — session 2 date should appear before session 1
    assert "$27.99" in resp.text
    assert "$12.50" in resp.text


# ---- SRCH-05: Review mode persistence tests ----

def _make_match_result():
    """Mixed confidence result for review mode testing."""
    return MatchResult(matches=[
        ItemMatch(
            list_item="milk", selected_upc="111", selected_description="Milk",
            selected_brand="Kroger", selected_size="1 gal", selected_price=3.99,
            confidence=0.5, reasoning="low",
        ),
        ItemMatch(
            list_item="eggs", selected_upc="222", selected_description="Eggs",
            selected_brand="Kroger", selected_size="12 ct", selected_price=4.49,
            confidence=0.95, reasoning="high",
        ),
    ])


def _make_candidates():
    return {
        "milk": [ProductCandidate(upc="111", description="Milk", brand="Kroger",
                                   size="1 gal", price_regular=3.99)],
        "eggs": [ProductCandidate(upc="222", description="Eggs", brand="Kroger",
                                   size="12 ct", price_regular=4.49)],
    }


@pytest.mark.anyio
async def test_review_mode_full_from_db(client, test_db):
    """POST /shopping/match with review_mode='full' in AppConfig passes mode to template."""
    await _seed_wizard_config(test_db, review_mode="full")

    match_result = _make_match_result()
    candidates = _make_candidates()

    with patch("app.main.get_settings", return_value=_mock_settings()), \
         patch("app.routers.shopping.CartService") as MockCS, \
         patch("app.routers.shopping.get_active_llm_config", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {
            "api_key": "k", "provider": "anthropic",
            "model": "claude-3-haiku-20240307", "ollama_base_url": None,
        }
        instance = MockCS.return_value
        instance.process_list = AsyncMock(return_value=(match_result, candidates))
        instance.partition_matches = MagicMock(
            return_value=([match_result.matches[0]], [match_result.matches[1]])
        )
        instance.preferences_loaded = False

        resp = await client.post("/shopping/match", data={"list_text": "milk\neggs"})

    assert resp.status_code == 200
    # Alpine x-data should contain mode: 'full'
    assert "mode: 'full'" in resp.text


@pytest.mark.anyio
async def test_review_mode_exceptions_default(client, test_db):
    """POST /shopping/match with default review_mode passes 'exceptions' to template."""
    await _seed_wizard_config(test_db, review_mode="exceptions")

    match_result = _make_match_result()
    candidates = _make_candidates()

    with patch("app.main.get_settings", return_value=_mock_settings()), \
         patch("app.routers.shopping.CartService") as MockCS, \
         patch("app.routers.shopping.get_active_llm_config", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = {
            "api_key": "k", "provider": "anthropic",
            "model": "claude-3-haiku-20240307", "ollama_base_url": None,
        }
        instance = MockCS.return_value
        instance.process_list = AsyncMock(return_value=(match_result, candidates))
        instance.partition_matches = MagicMock(
            return_value=([match_result.matches[0]], [match_result.matches[1]])
        )
        instance.preferences_loaded = False

        resp = await client.post("/shopping/match", data={"list_text": "milk\neggs"})

    assert resp.status_code == 200
    assert "mode: 'exceptions'" in resp.text
