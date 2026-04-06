"""Integration tests for /shopping/* HTTP endpoints.

These tests verify that each shopping router endpoint returns correct HTML
partial responses. All external services (Kroger API, LLM, OAuth) are mocked.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.config_model import AppConfig
from app.schemas.shopping import (
    ParsedListItem,
    ItemMatch,
    MatchResult,
    ProductCandidate,
)
from app.config import Settings


# ---------------------------------------------------------------------------
# Shared mock data
# ---------------------------------------------------------------------------

def _mock_settings():
    """Settings instance with test credentials to bypass middleware guards."""
    settings = MagicMock(spec=Settings)
    settings.kroger_client_id = "test_client_id"
    settings.kroger_client_secret = "test_client_secret"
    settings.llm_api_key = "test_llm_key"
    settings.llm_provider = "anthropic"
    settings.llm_model = "claude-3-haiku-20240307"
    settings.session_secret_key = "test_secret"
    settings.base_url = "http://testserver"
    return settings


def _make_match_result_mixed() -> MatchResult:
    """One low-confidence (review) + one high-confidence (auto) match."""
    return MatchResult(
        matches=[
            ItemMatch(
                list_item="milk",
                selected_upc="0001111111",
                selected_description="Kroger Whole Milk",
                selected_brand="Kroger",
                selected_size="1 gal",
                selected_price=3.99,
                confidence=0.70,  # -> review
                reasoning="Not very certain",
            ),
            ItemMatch(
                list_item="eggs",
                selected_upc="0002222222",
                selected_description="Kroger Large Eggs",
                selected_brand="Kroger",
                selected_size="12 ct",
                selected_price=4.49,
                confidence=0.92,  # -> auto
                reasoning="High confidence match",
            ),
        ]
    )


def _confirmed_items_json() -> str:
    """JSON string with one ConfirmedItem for /add-to-cart tests."""
    return json.dumps([
        {
            "upc": "0001111111",
            "description": "Kroger Whole Milk",
            "brand": "Kroger",
            "size": "1 gal",
            "quantity": 1,
            "price": 3.99,
        }
    ])


async def _seed_app_config(test_db):
    """Insert a fully configured AppConfig row into the test DB."""
    test_db.add(AppConfig(
        id=1,
        wizard_complete=True,
        wizard_step="complete",
        store_id="01400376",
        store_name="Fry's Marketplace",
        llm_provider="anthropic",
        llm_model="claude-3-haiku-20240307",
    ))
    await test_db.commit()


# ---------------------------------------------------------------------------
# Test 1 — Shopping page renders (SRCH-01)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_shopping_page_renders(client, test_db):
    """GET /shopping returns 200 with expected heading and form elements."""
    await _seed_app_config(test_db)
    with patch("app.main.get_settings", return_value=_mock_settings()):
        response = await client.get("/shopping")

    assert response.status_code == 200
    assert "What do you need?" in response.text
    assert "Build my cart" in response.text
    assert 'hx-post="/shopping/preview"' in response.text


# ---------------------------------------------------------------------------
# Test 2 — List preview (SRCH-01)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_list_preview(client, test_db):
    """POST /shopping/preview with items returns 'Parsed items' partial."""
    await _seed_app_config(test_db)
    with patch("app.main.get_settings", return_value=_mock_settings()):
        response = await client.post(
            "/shopping/preview",
            data={"list_text": "milk\neggs, a dozen"},
        )

    assert response.status_code == 200
    assert "Parsed items" in response.text


# ---------------------------------------------------------------------------
# Test 3 — Empty list preview returns empty HTML
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_list_preview_empty(client, test_db):
    """POST /shopping/preview with empty text returns empty HTML (no 'Parsed items')."""
    await _seed_app_config(test_db)
    with patch("app.main.get_settings", return_value=_mock_settings()):
        response = await client.post(
            "/shopping/preview",
            data={"list_text": ""},
        )

    assert response.status_code == 200
    assert "Parsed items" not in response.text


# ---------------------------------------------------------------------------
# Test 4 — Match returns review screen (SRCH-02, SRCH-04)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("app.services.cart_service.add_to_cart", new_callable=AsyncMock)
@patch("app.services.cart_service.match_products", new_callable=AsyncMock)
@patch("app.services.cart_service.search_products", new_callable=AsyncMock)
@patch("app.services.cart_service.parse_shopping_list", new_callable=AsyncMock)
async def test_match_returns_review_screen(
    mock_parse, mock_search, mock_match, mock_add, client, test_db
):
    """POST /shopping/match returns review_screen with review + auto zones."""
    await _seed_app_config(test_db)

    mock_parse.return_value = [
        ParsedListItem(name="milk", quantity=1),
        ParsedListItem(name="eggs", quantity=1),
    ]
    mock_search.return_value = []
    mock_match.return_value = _make_match_result_mixed()

    with patch("app.main.get_settings", return_value=_mock_settings()):
        response = await client.post(
            "/shopping/match",
            data={"list_text": "milk\neggs"},
        )

    assert response.status_code == 200
    assert "Review your matches" in response.text
    assert "Review these matches" in response.text   # low-confidence zone
    assert "Auto-matched" in response.text            # high-confidence zone


# ---------------------------------------------------------------------------
# Test 5 — Review screen has Alpine toggle (SRCH-05)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("app.services.cart_service.add_to_cart", new_callable=AsyncMock)
@patch("app.services.cart_service.match_products", new_callable=AsyncMock)
@patch("app.services.cart_service.search_products", new_callable=AsyncMock)
@patch("app.services.cart_service.parse_shopping_list", new_callable=AsyncMock)
async def test_review_screen_has_toggle(
    mock_parse, mock_search, mock_match, mock_add, client, test_db
):
    """Review screen shows Exceptions only/Full review toggle when both zones present."""
    await _seed_app_config(test_db)

    mock_parse.return_value = [
        ParsedListItem(name="milk", quantity=1),
        ParsedListItem(name="eggs", quantity=1),
    ]
    mock_search.return_value = []
    mock_match.return_value = _make_match_result_mixed()

    with patch("app.main.get_settings", return_value=_mock_settings()):
        response = await client.post(
            "/shopping/match",
            data={"list_text": "milk\neggs"},
        )

    assert response.status_code == 200
    assert "Exceptions only" in response.text
    assert "Full review" in response.text
    assert "x-data" in response.text   # Alpine.js data binding present


# ---------------------------------------------------------------------------
# Test 6 — Empty list match returns error block
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_match_empty_list_returns_error(client, test_db):
    """POST /shopping/match with whitespace-only text returns 'Your list is empty'."""
    await _seed_app_config(test_db)
    with patch("app.main.get_settings", return_value=_mock_settings()):
        response = await client.post(
            "/shopping/match",
            data={"list_text": "   "},
        )

    assert response.status_code == 200
    assert "Your list is empty" in response.text


# ---------------------------------------------------------------------------
# Test 7 — Add to cart flow (CART-01)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("app.services.cart_service.add_to_cart", new_callable=AsyncMock)
@patch("app.routers.shopping.get_valid_access_token", new_callable=AsyncMock)
async def test_add_to_cart_flow(mock_token, mock_add, client, test_db):
    """POST /shopping/add-to-cart with valid items returns success screen (CART-01)."""
    await _seed_app_config(test_db)
    mock_token.return_value = "fake-access-token"
    mock_add.return_value = (True, "")

    with patch("app.main.get_settings", return_value=_mock_settings()):
        response = await client.post(
            "/shopping/add-to-cart",
            data={"confirmed_items_json": _confirmed_items_json()},
        )

    assert response.status_code == 200
    assert "Items added to your cart" in response.text


# ---------------------------------------------------------------------------
# Test 8 — Success screen shows items and CTA (CART-03)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("app.services.cart_service.add_to_cart", new_callable=AsyncMock)
@patch("app.routers.shopping.get_valid_access_token", new_callable=AsyncMock)
async def test_success_screen_shows_items(mock_token, mock_add, client, test_db):
    """Success screen shows Fry's link and 'Show added items' (CART-03)."""
    await _seed_app_config(test_db)
    mock_token.return_value = "fake-access-token"
    mock_add.return_value = (True, "")

    with patch("app.main.get_settings", return_value=_mock_settings()):
        response = await client.post(
            "/shopping/add-to-cart",
            data={"confirmed_items_json": _confirmed_items_json()},
        )

    assert response.status_code == 200
    assert "Open Fry's curbside pickup" in response.text
    assert "Show added items" in response.text


# ---------------------------------------------------------------------------
# Test 9 — Expired token returns reconnect prompt
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("app.routers.shopping.get_valid_access_token", new_callable=AsyncMock)
async def test_add_to_cart_expired_token(mock_token, client, test_db):
    """When access token is None, response contains session expired / Reconnect."""
    await _seed_app_config(test_db)
    mock_token.return_value = None

    with patch("app.main.get_settings", return_value=_mock_settings()):
        response = await client.post(
            "/shopping/add-to-cart",
            data={"confirmed_items_json": _confirmed_items_json()},
        )

    assert response.status_code == 200
    # The error_block contains "Session expired" heading and "Reconnect" link
    assert "Session expired" in response.text or "session expired" in response.text.lower()
    assert "Reconnect" in response.text
