"""Integration tests for /preferences/* HTTP endpoints and CartService preference wiring.

All LLM and Kroger API calls are mocked. Tests use the client fixture (AsyncClient +
test_db) from conftest. Pattern follows test_shopping_flow.py.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select

from app.models.config_model import AppConfig
from app.models.preference_entry import PreferenceEntry
from app.schemas.preferences import ParsedReceipt, ReceiptLineItem, PreferenceDelta
from app.schemas.shopping import ParsedListItem, ItemMatch, MatchResult
from app.services.cart_service import CartService
from app.config import Settings


def _mock_settings():
    """Settings with test credentials to bypass SetupGuardMiddleware."""
    settings = MagicMock(spec=Settings)
    settings.kroger_client_id = "test_client_id"
    settings.kroger_client_secret = "test_client_secret"
    settings.llm_api_key = "test_llm_key"
    settings.llm_provider = "anthropic"
    settings.llm_model = "claude-haiku-4-5-20251001"
    settings.session_secret_key = "test_secret"
    settings.base_url = "http://testserver"
    return settings


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

async def _seed_app_config(db):
    """Seed AppConfig so SetupGuardMiddleware passes."""
    config = AppConfig(
        wizard_complete=True,
        store_id="70100153",
        store_name="Fry's Marketplace",
        llm_provider="anthropic",
        llm_model="claude-haiku-4-5-20251001",
    )
    db.add(config)
    await db.commit()


async def _seed_preference(
    db,
    category: str = "milk",
    brand: str = "Organic Valley",
    name: str = "2% Milk",
    count: int = 1,
    source: str = "receipt",
) -> PreferenceEntry:
    """Seed a single PreferenceEntry for test setup."""
    entry = PreferenceEntry(
        product_category=category,
        brand=brand,
        product_name=name,
        purchase_count=count,
        source=source,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


def _make_cart_service(test_db) -> CartService:
    return CartService(
        db=test_db,
        location_id="70100153",
        kroger_client_id="fake_client_id",
        kroger_client_secret="fake_client_secret",
        llm_api_key="fake_llm_key",
        llm_provider="anthropic",
        llm_model="claude-haiku-4-5-20251001",
    )


KROGER_PRODUCT_DICT = {
    "productId": "0001234500000",
    "description": "Organic Valley 2% Milk",
    "brand": "Organic Valley",
    "items": [{"size": "1 gal", "price": {"regular": 5.99}}],
    "images": [],
    "fulfillment": {"csp": True},
}


# ---------------------------------------------------------------------------
# Test 1 — GET /preferences returns 200 with "Preferences"
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_preferences_page_loads(client, test_db):
    """GET /preferences returns 200 with 'Preferences' heading."""
    await _seed_app_config(test_db)
    with patch("app.main.get_settings", return_value=_mock_settings()):
        response = await client.get("/preferences")
    assert response.status_code == 200
    assert "Preferences" in response.text


# ---------------------------------------------------------------------------
# Test 2 — POST /preferences/upload with mock PDF returns review HTML
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_upload_receipt(client, test_db):
    """POST /preferences/upload with a mock PDF returns receipt review HTML with parsed items."""
    await _seed_app_config(test_db)

    mock_receipt = ParsedReceipt(
        items=[
            ReceiptLineItem(
                product_name="Medium Cheddar",
                brand="Tillamook",
                product_category="cheddar cheese",
                confidence=0.95,
                price=8.49,
            ),
            ReceiptLineItem(
                product_name="2% Milk",
                brand="Organic Valley",
                product_category="milk",
                confidence=0.90,
                price=4.99,
            ),
        ],
        parse_warnings=[],
    )

    with patch("app.main.get_settings", return_value=_mock_settings()):
        with patch("app.routers.preferences.extract_receipt_text",
                   return_value=("FRYS STORE #123\nTILLAMOOK CHEDDAR $8.49\nORG VALLEY MILK $4.99\nTOTAL $14.00", [])):
            with patch("app.routers.preferences.parse_receipt_with_llm",
                       new=AsyncMock(return_value=mock_receipt)):
                response = await client.post(
                    "/preferences/upload",
                    files={"receipt_pdf": ("receipt.pdf", b"fake pdf content", "application/pdf")},
                )

    assert response.status_code == 200
    # Response should contain the parsed item names
    assert "Tillamook" in response.text or "Medium Cheddar" in response.text


# ---------------------------------------------------------------------------
# Test 3 — POST /preferences/upload with non-PDF returns error message
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_upload_invalid_file(client, test_db):
    """POST /preferences/upload when extract_receipt_text returns short text shows error."""
    await _seed_app_config(test_db)

    with patch("app.main.get_settings", return_value=_mock_settings()):
        with patch("app.routers.preferences.extract_receipt_text", return_value=("", ["PDF extraction failed: not a PDF"])):
            response = await client.post(
                "/preferences/upload",
                files={"receipt_pdf": ("notapdf.txt", b"not a pdf", "text/plain")},
            )

    assert response.status_code == 200
    # Should render the error state (not a valid receipt)
    assert "Could not read" in response.text or "error" in response.text.lower() or "couldn" in response.text.lower()


# ---------------------------------------------------------------------------
# Test 4 — Preference CRUD lifecycle
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_preference_crud(client, test_db):
    """Full CRUD lifecycle: create, list, update, delete."""
    await _seed_app_config(test_db)

    with patch("app.main.get_settings", return_value=_mock_settings()):
        # CREATE
        create_response = await client.post(
            "/preferences/create",
            data={
                "product_name": "2% Milk",
                "brand": "Organic Valley",
                "product_category": "milk",
                "notes": "",
            },
        )
        assert create_response.status_code == 200
        assert "Organic Valley" in create_response.text

        # LIST — verify preference appears
        list_response = await client.get("/preferences/list")
        assert list_response.status_code == 200
        assert "Organic Valley" in list_response.text

        # Find the entry ID from DB to use in update/delete
        from sqlalchemy import select
        result = await test_db.execute(
            select(PreferenceEntry).where(PreferenceEntry.brand == "Organic Valley")
        )
        entry = result.scalar_one()
        pref_id = entry.id

        # UPDATE
        update_response = await client.put(
            f"/preferences/{pref_id}",
            data={
                "product_name": "Whole Milk",
                "brand": "Straus Family",
                "product_category": "milk",
                "notes": "",
            },
        )
        assert update_response.status_code == 200
        assert "Straus Family" in update_response.text

        # DELETE
        delete_response = await client.delete(f"/preferences/{pref_id}")
        assert delete_response.status_code == 200


# ---------------------------------------------------------------------------
# Test 5 — GET /preferences/list?q=Tillamook returns filtered results
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_preference_search(client, test_db):
    """GET /preferences/list?q=Tillamook returns only matching preference."""
    await _seed_app_config(test_db)
    await _seed_preference(test_db, brand="Tillamook", category="cheddar cheese", name="Medium Cheddar")
    await _seed_preference(test_db, brand="Organic Valley", category="milk", name="2% Milk")

    with patch("app.main.get_settings", return_value=_mock_settings()):
        response = await client.get("/preferences/list?q=Tillamook")
    assert response.status_code == 200
    assert "Tillamook" in response.text
    assert "Organic Valley" not in response.text


# ---------------------------------------------------------------------------
# Test 6 — Bulk delete preferences
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_bulk_delete_preferences(client, test_db):
    """POST /preferences/bulk-delete with IDs removes them and returns empty list."""
    await _seed_app_config(test_db)
    e1 = await _seed_preference(test_db, brand="Brand1", category="cat1", name="Prod1")
    e2 = await _seed_preference(test_db, brand="Brand2", category="cat2", name="Prod2")
    e3 = await _seed_preference(test_db, brand="Brand3", category="cat3", name="Prod3")

    with patch("app.main.get_settings", return_value=_mock_settings()):
        response = await client.post(
            "/preferences/bulk-delete",
            data={"ids": f"{e1.id},{e2.id},{e3.id}"},
        )
    assert response.status_code == 200

    # All three deleted — list should be empty
    result = await test_db.execute(select(PreferenceEntry))
    remaining = list(result.scalars().all())
    assert len(remaining) == 0


# ---------------------------------------------------------------------------
# Test 7 — NL chat: clarify action returns question
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_nl_chat_clarify(client, test_db):
    """POST /preferences/chat with ambiguous message returns clarification question."""
    await _seed_app_config(test_db)

    mock_delta = PreferenceDelta(
        action="clarify",
        clarification_question="Which brand of oat milk do you prefer?",
        human_summary="Clarification needed",
        category="",
    )

    with patch("app.main.get_settings", return_value=_mock_settings()):
        with patch("app.routers.preferences.parse_preference_nl",
                   new=AsyncMock(return_value=mock_delta)):
            response = await client.post(
                "/preferences/chat",
                data={"message": "oat milk"},
            )

    assert response.status_code == 200
    assert "Which brand of oat milk" in response.text


# ---------------------------------------------------------------------------
# Test 8 — NL chat: confirm + apply saves preference to DB
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_nl_chat_confirm(client, test_db):
    """POST /preferences/chat with clear intent shows 'Apply' button; POST /chat/apply saves to DB."""
    await _seed_app_config(test_db)

    mock_delta = PreferenceDelta(
        action="add",
        category="milk",
        new_brand="Oatly",
        product_name="Oat Milk",
        human_summary="Add Oatly Oat Milk as a preference",
    )

    # Step 1: post a message — should get confirmation preview
    with patch("app.main.get_settings", return_value=_mock_settings()):
        with patch("app.routers.preferences.parse_preference_nl",
                   new=AsyncMock(return_value=mock_delta)):
            chat_response = await client.post(
                "/preferences/chat",
                data={"message": "we switched to oat milk from Oatly"},
            )

    assert chat_response.status_code == 200
    # Response should contain "Apply" button for the confirmed delta
    assert "Apply" in chat_response.text or "apply" in chat_response.text.lower()

    # Step 2: apply the change
    with patch("app.main.get_settings", return_value=_mock_settings()):
        apply_response = await client.post("/preferences/chat/apply")
    assert apply_response.status_code == 200
    assert "Done" in apply_response.text or "updated" in apply_response.text.lower()

    # Verify preference was saved to DB
    result = await test_db.execute(
        select(PreferenceEntry).where(
            PreferenceEntry.product_category == "milk",
            PreferenceEntry.brand == "Oatly",
        )
    )
    entry = result.scalar_one_or_none()
    assert entry is not None
    assert entry.source == "nl_chat"


# ---------------------------------------------------------------------------
# Test 9 — CartService.process_list auto-loads preferences (PREF-06)
# ---------------------------------------------------------------------------

async def _seed_app_config_custom(db, provider: str, model: str):
    """Seed AppConfig with wizard_complete=True and a custom LLM provider/model."""
    config = AppConfig(
        wizard_complete=True,
        store_id="70100153",
        store_name="Fry's Marketplace",
        llm_provider=provider,
        llm_model=model,
    )
    db.add(config)
    await db.commit()


# ---------------------------------------------------------------------------
# Test 10 — upload_receipt uses DB LLM config (LLM-CONFIG)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_upload_receipt_uses_db_llm_config(client, test_db):
    """POST /preferences/upload uses DB-configured LLM provider/model, not env defaults."""
    await _seed_app_config_custom(test_db, "openai", "gpt-4o")

    with patch("app.main.get_settings", return_value=_mock_settings()):
        with patch("app.routers.preferences.extract_receipt_text",
                   return_value=("FRYS STORE #123\nItem1 $5.00\nItem2 $3.50\nItem3 $2.00\nSUBTOTAL $10.50\nTAX $0.84\nTOTAL $11.34", [])):
            with patch("app.routers.preferences.parse_receipt_with_llm",
                       new=AsyncMock(return_value=ParsedReceipt(items=[], parse_warnings=[]))) as mock_parse:
                response = await client.post(
                    "/preferences/upload",
                    files={"receipt_pdf": ("receipt.pdf", b"fake pdf content", "application/pdf")},
                )

    assert response.status_code == 200
    mock_parse.assert_called_once()
    call_args = mock_parse.call_args
    # Positional args: (raw_text, api_key, provider, model)
    assert call_args[0][2] == "openai", f"Expected provider='openai', got {call_args[0][2]!r}"
    assert call_args[0][3] == "gpt-4o", f"Expected model='gpt-4o', got {call_args[0][3]!r}"


# ---------------------------------------------------------------------------
# Test 11 — preference_chat uses DB LLM config (LLM-CONFIG)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_nl_chat_uses_db_llm_config(client, test_db):
    """POST /preferences/chat uses DB-configured LLM provider/model, not env defaults."""
    await _seed_app_config_custom(test_db, "openai", "gpt-4o")

    mock_delta = PreferenceDelta(
        action="clarify",
        human_summary="What kind?",
        clarification_question="What kind of oat milk?",
    )

    with patch("app.main.get_settings", return_value=_mock_settings()):
        with patch("app.routers.preferences.parse_preference_nl",
                   new=AsyncMock(return_value=mock_delta)) as mock_nl:
            response = await client.post(
                "/preferences/chat",
                data={"message": "switch to oat milk"},
            )

    assert response.status_code == 200
    mock_nl.assert_called_once()
    call_args = mock_nl.call_args
    # Positional args: (conversation_history, api_key, provider, model)
    assert call_args[0][2] == "openai", f"Expected provider='openai', got {call_args[0][2]!r}"
    assert call_args[0][3] == "gpt-4o", f"Expected model='gpt-4o', got {call_args[0][3]!r}"

@pytest.mark.anyio
@patch("app.services.cart_service.match_products", new_callable=AsyncMock)
@patch("app.services.cart_service.search_products", new_callable=AsyncMock)
@patch("app.services.cart_service.parse_shopping_list", new_callable=AsyncMock)
async def test_process_list_with_preferences(mock_parse, mock_search, mock_match, test_db):
    """CartService.process_list auto-loads established preferences and passes them to match_products."""
    # Seed 2 established preference entries (count=3 = established)
    await _seed_preference(test_db, category="cheddar cheese", brand="Tillamook", name="Medium Cheddar", count=3)
    await _seed_preference(test_db, category="milk", brand="Organic Valley", name="2% Milk", count=3)

    mock_parse.return_value = [
        ParsedListItem(name="milk", quantity=1),
        ParsedListItem(name="cheese", quantity=1),
    ]
    mock_search.return_value = [KROGER_PRODUCT_DICT]
    mock_match.return_value = MatchResult(
        matches=[
            ItemMatch(
                list_item="milk",
                selected_upc="0001234500000",
                selected_description="Organic Valley 2% Milk",
                selected_brand="Organic Valley",
                selected_size="1 gal",
                selected_price=5.99,
                confidence=0.92,
                reasoning="Matches user preference",
            ),
        ]
    )

    service = _make_cart_service(test_db)
    await service.process_list("milk, cheese")

    # Verify match_products was called with a non-None preferences kwarg
    mock_match.assert_called_once()
    call_kwargs = mock_match.call_args.kwargs
    assert "preferences" in call_kwargs, "match_products must receive preferences kwarg"
    assert call_kwargs["preferences"] is not None, "preferences must not be None when established entries exist"

    # Verify entries dict contains our seeded preferences
    entries = call_kwargs["preferences"]["entries"]
    assert len(entries) == 2

    # Verify the preferences_loaded flag is set
    assert service.preferences_loaded is True
