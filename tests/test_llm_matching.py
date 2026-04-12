"""Unit tests for LLM-powered shopping list parsing and product matching.

All tests mock the Instructor client to avoid real LLM API calls.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.llm_service import (
    parse_shopping_list,
    match_products,
    _build_matching_prompt,
)
from app.schemas.shopping import (
    ItemMatch,
    MatchResult,
    ParsedListItem,
    ProductCandidate,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Reusable schema for ParsedList — mirrors the module-level class
class _ParsedListStub:
    def __init__(self, items):
        self.items = items


def _make_mock_client(return_value):
    """Create a mock Instructor async client that returns the given value."""
    mock_client = MagicMock()
    mock_client.create = AsyncMock(return_value=return_value)
    return mock_client


def _make_candidates() -> dict[str, list[ProductCandidate]]:
    return {
        "milk": [
            ProductCandidate(
                upc="001",
                description="Kroger 2% Milk",
                brand="Kroger",
                size="1 gal",
                price_regular=3.49,
            ),
            ProductCandidate(
                upc="002",
                description="Organic Valley 2% Milk",
                brand="Organic Valley",
                size="1/2 gal",
                price_regular=5.99,
            ),
        ],
        "eggs": [
            ProductCandidate(
                upc="004",
                description="Kroger Large Eggs",
                brand="Kroger",
                size="12 ct",
                price_regular=2.99,
            ),
            ProductCandidate(
                upc="005",
                description="Vital Farms Large Eggs",
                brand="Vital Farms",
                size="12 ct",
                price_regular=7.49,
            ),
        ],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_parse_shopping_list_returns_parsed_items():
    """parse_shopping_list() returns a list of ParsedListItem from mocked Instructor."""
    parsed_items = [
        ParsedListItem(name="milk", quantity=1, notes="2% fat"),
        ParsedListItem(name="eggs", quantity=12),
    ]
    mock_result = _ParsedListStub(items=parsed_items)

    with patch("app.services.llm_service.instructor.from_provider", return_value=_make_mock_client(mock_result)):
        result = await parse_shopping_list(
            raw_text="1 gallon 2% milk\na dozen eggs",
            api_key="test_key",
        )

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0].name == "milk"
    assert result[1].quantity == 12


@pytest.mark.anyio
async def test_match_products_returns_match_result():
    """match_products() returns a MatchResult with per-item selections and confidence."""
    mock_result = MatchResult(
        matches=[
            ItemMatch(
                list_item="milk",
                selected_upc="001",
                selected_description="Kroger 2% Milk",
                confidence=0.95,
                reasoning="exact match",
                alternatives=["002", "003"],
            ),
            ItemMatch(
                list_item="eggs",
                selected_upc="004",
                selected_description="Kroger Large Eggs",
                confidence=0.6,
                reasoning="multiple size options",
                alternatives=["005"],
            ),
        ]
    )

    with patch("app.services.llm_service.instructor.from_provider", return_value=_make_mock_client(mock_result)):
        result = await match_products(
            list_items=[
                ParsedListItem(name="milk", quantity=1),
                ParsedListItem(name="eggs", quantity=12),
            ],
            candidates=_make_candidates(),
            api_key="test_key",
        )

    assert isinstance(result, MatchResult)
    assert len(result.matches) == 2
    assert result.matches[0].confidence == 0.95
    assert result.matches[1].confidence == 0.6


@pytest.mark.anyio
async def test_match_products_accepts_preferences_none():
    """match_products() accepts preferences=None without error (D-07 Phase 3 hook)."""
    mock_result = MatchResult(matches=[])

    with patch("app.services.llm_service.instructor.from_provider", return_value=_make_mock_client(mock_result)):
        result = await match_products(
            list_items=[ParsedListItem(name="milk", quantity=1)],
            candidates={"milk": []},
            api_key="test_key",
            preferences=None,
        )

    assert isinstance(result, MatchResult)


@pytest.mark.anyio
async def test_match_products_accepts_preferences_dict():
    """match_products() accepts a preferences dict and includes it in the system prompt."""
    mock_result = MatchResult(matches=[])
    captured_messages = []

    async def capture_create(**kwargs):
        captured_messages.append(kwargs.get("messages", []))
        return mock_result

    mock_client = MagicMock()
    mock_client.create = capture_create

    with patch("app.services.llm_service.instructor.from_provider", return_value=mock_client):
        result = await match_products(
            list_items=[ParsedListItem(name="milk", quantity=1)],
            candidates={"milk": []},
            api_key="test_key",
            preferences={"milk": "Organic Valley"},
        )

    assert isinstance(result, MatchResult)
    # The system prompt (first message) should mention preferences
    assert len(captured_messages) == 1
    system_content = captured_messages[0][0]["content"]
    assert "Organic Valley" in system_content


@pytest.mark.anyio
async def test_provider_model_strings():
    """LLM-01: verify correct model string construction for three providers."""
    mock_result = _ParsedListStub(items=[])
    captured_provider_args = []

    def capture_from_provider(provider_str, **kwargs):
        captured_provider_args.append(provider_str)
        return _make_mock_client(mock_result)

    with patch("app.services.llm_service.instructor.from_provider", side_effect=capture_from_provider):
        # anthropic
        await parse_shopping_list("milk", api_key="k", provider="anthropic", model="claude-haiku-4-5-20251001")
        # openai
        await parse_shopping_list("milk", api_key="k", provider="openai", model="gpt-4o-mini")
        # ollama
        await parse_shopping_list("milk", api_key="k", provider="ollama", model="llama3")

    assert captured_provider_args[0] == "litellm/anthropic/claude-haiku-4-5-20251001"
    assert captured_provider_args[1] == "litellm/openai/gpt-4o-mini"
    assert captured_provider_args[2] == "litellm/ollama/llama3"


def test_build_matching_prompt_format():
    """_build_matching_prompt() formats items correctly and excludes display-only fields."""
    items = [ParsedListItem(name="milk", quantity=1, notes="2% fat")]
    candidates = {
        "milk": [
            ProductCandidate(
                upc="001",
                description="Kroger 2% Milk",
                brand="Kroger",
                size="1 gal",
                price_regular=3.49,
                thumbnail_url="https://example.com/milk.jpg",
            )
        ]
    }

    prompt = _build_matching_prompt(items, candidates)

    assert "Item: milk" in prompt
    assert "UPC: 001" in prompt
    assert "3.49" in prompt
    assert "thumbnail_url" not in prompt
    assert "https://example.com" not in prompt


@pytest.mark.anyio
async def test_parse_shopping_list_error_handling():
    """parse_shopping_list() wraps LLM exceptions as RuntimeError with descriptive message."""
    def raise_error(*args, **kwargs):
        raise ValueError("connection timeout")

    mock_client = MagicMock()
    mock_client.create = AsyncMock(side_effect=raise_error)

    with patch("app.services.llm_service.instructor.from_provider", return_value=mock_client):
        with pytest.raises(RuntimeError) as exc_info:
            await parse_shopping_list("milk", api_key="bad_key")

    assert "Failed to parse" in str(exc_info.value)
