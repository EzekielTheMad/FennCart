"""Unit tests for CartService: confidence partitioning, pipeline orchestration,
search deduplication, cart persistence, and candidate extraction.

All external calls (kroger_client, llm_service) are mocked — these are unit
tests of CartService logic only.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import select

from app.services.cart_service import CartService
from app.schemas.shopping import (
    ParsedListItem,
    ProductCandidate,
    ItemMatch,
    MatchResult,
    ConfirmedItem,
)
from app.models.cart_session import CartSession
from app.models.cart_item import CartItem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_item_match(name: str, upc: str, confidence: float) -> ItemMatch:
    return ItemMatch(
        list_item=name,
        selected_upc=upc,
        selected_description=f"{name} product",
        selected_brand="TestBrand",
        selected_size="1 unit",
        selected_price=2.99,
        confidence=confidence,
        reasoning="test",
    )


def _make_confirmed_item(upc: str = "012345", qty: int = 1) -> ConfirmedItem:
    return ConfirmedItem(
        upc=upc,
        description="Test Item",
        brand="TestBrand",
        size="1 unit",
        quantity=qty,
        price=2.99,
    )


def _make_cart_service(test_db) -> CartService:
    return CartService(
        db=test_db,
        location_id="01400376",
        kroger_client_id="fake_client_id",
        kroger_client_secret="fake_client_secret",
        llm_api_key="fake_llm_key",
        llm_provider="anthropic",
        llm_model="claude-haiku-4-5-20251001",
    )


KROGER_PRODUCT_DICT = {
    "productId": "0001234500000",
    "description": "Kroger Whole Milk",
    "brand": "Kroger",
    "items": [
        {
            "size": "1 gal",
            "price": {"regular": 3.99, "promo": 2.99},
        }
    ],
    "images": [
        {
            "perspective": "front",
            "sizes": [
                {"size": "thumbnail", "url": "https://example.com/milk-thumb.jpg"},
                {"size": "small", "url": "https://example.com/milk-small.jpg"},
            ],
        }
    ],
    "fulfillment": {"csp": True},
}


# ---------------------------------------------------------------------------
# Test 1 — Confidence partitioning (SRCH-04)
# ---------------------------------------------------------------------------

def test_confidence_partitioning():
    """partition_matches splits at 0.8: < 0.8 -> review, >= 0.8 -> auto."""
    service = CartService(
        db=MagicMock(),
        location_id="01400376",
        kroger_client_id="id",
        kroger_client_secret="secret",
        llm_api_key="key",
    )

    match_result = MatchResult(
        matches=[
            _make_item_match("eggs", "upc-a", confidence=0.95),
            _make_item_match("milk", "upc-b", confidence=0.75),
            _make_item_match("butter", "upc-c", confidence=0.85),
        ]
    )

    review_items, auto_items = service.partition_matches(match_result)

    assert len(review_items) == 1, "Only the 0.75 item should need review"
    assert len(auto_items) == 2, "The 0.95 and 0.85 items should be auto"
    assert review_items[0].confidence == 0.75
    # Both auto items have confidence >= 0.8
    for item in auto_items:
        assert item.confidence >= 0.8


# ---------------------------------------------------------------------------
# Test 2 — process_list calls search and match (SRCH-02)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("app.services.cart_service.match_products", new_callable=AsyncMock)
@patch("app.services.cart_service.search_products", new_callable=AsyncMock)
@patch("app.services.cart_service.parse_shopping_list", new_callable=AsyncMock)
async def test_process_list_calls_search_and_match(
    mock_parse, mock_search, mock_match, test_db
):
    """process_list calls parse, search, and match exactly once each for a list."""
    mock_parse.return_value = [ParsedListItem(name="milk", quantity=1, notes="2%")]
    mock_search.return_value = [KROGER_PRODUCT_DICT]
    mock_match.return_value = MatchResult(
        matches=[_make_item_match("milk", "0001234500000", 0.92)]
    )

    service = _make_cart_service(test_db)
    result = await service.process_list("milk")

    # Returns a tuple of (MatchResult, candidates_dict)
    assert isinstance(result, tuple)
    assert len(result) == 2
    match_result, candidates_dict = result
    assert isinstance(match_result, MatchResult)
    assert isinstance(candidates_dict, dict)

    mock_parse.assert_called_once()
    mock_search.assert_called_once()
    mock_match.assert_called_once()


# ---------------------------------------------------------------------------
# Test 3 — Search deduplication
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("app.services.cart_service.match_products", new_callable=AsyncMock)
@patch("app.services.cart_service.search_products", new_callable=AsyncMock)
@patch("app.services.cart_service.parse_shopping_list", new_callable=AsyncMock)
async def test_search_deduplication(mock_parse, mock_search, mock_match, test_db):
    """Duplicate items in list should only trigger one search_products call."""
    # Return two items with the same name "milk"
    mock_parse.return_value = [
        ParsedListItem(name="milk", quantity=1),
        ParsedListItem(name="milk", quantity=2),
    ]
    mock_search.return_value = [KROGER_PRODUCT_DICT]
    mock_match.return_value = MatchResult(
        matches=[_make_item_match("milk", "0001234500000", 0.92)]
    )

    service = _make_cart_service(test_db)
    await service.process_list("milk\nmilk")

    # search_products should only be called once due to in-memory dedup cache
    assert mock_search.call_count == 1, (
        f"Expected 1 search call (dedup), got {mock_search.call_count}"
    )


# ---------------------------------------------------------------------------
# Test 4 — Cart items persisted on success (CART-02)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("app.services.cart_service.add_to_cart", new_callable=AsyncMock)
async def test_cart_items_persisted(mock_add, test_db):
    """add_confirmed_to_cart saves CartSession + CartItems even on Kroger success."""
    mock_add.return_value = (True, "")

    confirmed = [
        _make_confirmed_item(upc="000000001", qty=1),
        _make_confirmed_item(upc="000000002", qty=2),
    ]

    service = _make_cart_service(test_db)
    session_record, success_count, fail_count, error_msg = (
        await service.add_confirmed_to_cart(confirmed, "fake-token")
    )

    assert success_count == 2
    assert fail_count == 0
    assert error_msg == ""

    # Verify CartSession persisted
    session_result = await test_db.execute(
        select(CartSession).where(CartSession.id == session_record.id)
    )
    db_session = session_result.scalar_one_or_none()
    assert db_session is not None
    assert db_session.item_count == 2

    # Verify CartItems persisted
    items_result = await test_db.execute(
        select(CartItem).where(CartItem.session_id == session_record.id)
    )
    db_items = list(items_result.scalars().all())
    assert len(db_items) == 2
    upcs = {item.upc for item in db_items}
    assert "000000001" in upcs
    assert "000000002" in upcs


# ---------------------------------------------------------------------------
# Test 5 — Cart items persisted on Kroger failure
# ---------------------------------------------------------------------------

@pytest.mark.anyio
@patch("app.services.cart_service.add_to_cart", new_callable=AsyncMock)
async def test_cart_items_persisted_on_failure(mock_add, test_db):
    """CartItems are saved locally even when Kroger add_to_cart returns failure."""
    mock_add.return_value = (False, "Kroger API error")

    confirmed = [_make_confirmed_item(upc="000000099", qty=1)]

    service = _make_cart_service(test_db)
    session_record, success_count, fail_count, error_msg = (
        await service.add_confirmed_to_cart(confirmed, "fake-token")
    )

    assert success_count == 0
    assert fail_count == len(confirmed)
    assert "error" in error_msg.lower()

    # CartItems should still exist in DB (local shadow)
    items_result = await test_db.execute(
        select(CartItem).where(CartItem.session_id == session_record.id)
    )
    db_items = list(items_result.scalars().all())
    assert len(db_items) == 1, "Local CartItem shadow must persist even on Kroger failure"
    assert db_items[0].upc == "000000099"


# ---------------------------------------------------------------------------
# Test 6 — get_session_items (CART-03)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_session_items(test_db):
    """get_session_items returns the CartSession and its CartItems."""
    # Seed DB directly
    session_record = CartSession(item_count=2, estimated_total=5.98)
    test_db.add(session_record)
    await test_db.flush()

    test_db.add(CartItem(
        session_id=session_record.id,
        upc="111111111",
        description="Whole Milk",
        brand="Kroger",
        size="1 gal",
        quantity=1,
        price_regular=3.99,
    ))
    test_db.add(CartItem(
        session_id=session_record.id,
        upc="222222222",
        description="Large Eggs",
        brand="Vital Farms",
        size="12 ct",
        quantity=1,
        price_regular=5.49,
    ))
    await test_db.commit()

    service = _make_cart_service(test_db)
    returned_session, returned_items = await service.get_session_items(session_record.id)

    assert returned_session is not None
    assert returned_session.id == session_record.id
    assert returned_session.item_count == 2
    assert len(returned_items) == 2

    upcs = {item.upc for item in returned_items}
    assert "111111111" in upcs
    assert "222222222" in upcs


# ---------------------------------------------------------------------------
# Test 7 — _to_candidate field extraction
# ---------------------------------------------------------------------------

def test_to_candidate_extracts_fields():
    """_to_candidate maps all Kroger product dict fields to ProductCandidate."""
    candidate = CartService._to_candidate(KROGER_PRODUCT_DICT)

    assert isinstance(candidate, ProductCandidate)
    assert candidate.upc == "0001234500000"
    assert candidate.description == "Kroger Whole Milk"
    assert candidate.brand == "Kroger"
    assert candidate.size == "1 gal"
    assert candidate.price_regular == 3.99
    assert candidate.price_promo == 2.99
    assert candidate.thumbnail_url == "https://example.com/milk-thumb.jpg"


def test_to_candidate_handles_missing_fields():
    """_to_candidate is defensive: returns empty/None when nested fields are absent."""
    sparse_product = {"productId": "0009999", "description": "Mystery Item"}
    candidate = CartService._to_candidate(sparse_product)

    assert candidate.upc == "0009999"
    assert candidate.description == "Mystery Item"
    assert candidate.brand == ""
    assert candidate.size == ""
    assert candidate.price_regular is None
    assert candidate.price_promo is None
    assert candidate.thumbnail_url is None
