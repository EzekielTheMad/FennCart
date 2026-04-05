import json
from typing import Optional

import instructor
import litellm
from pydantic import BaseModel

from app.schemas.shopping import ItemMatch, MatchResult, ParsedListItem, ProductCandidate


class ParsedList(BaseModel):
    """Wrapper for Instructor to return a list of parsed shopping items."""

    items: list[ParsedListItem]


async def test_connection(
    api_key: str,
    provider: str = "anthropic",
    model: str = "claude-3-haiku-20240307",
    base_url: Optional[str] = None,
) -> tuple[bool, str]:
    """Test LLM API key by sending a minimal completion request.

    When base_url is provided (Ollama), it is passed as api_base and
    the api_key is not sent (Ollama does not require API keys).

    Returns (success: bool, message: str).
    """
    try:
        # Build model string for LiteLLM: provider/model
        model_str = f"{provider}/{model}" if "/" not in model else model
        kwargs: dict = {
            "model": model_str,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 5,
        }
        if base_url:
            kwargs["api_base"] = base_url
        else:
            kwargs["api_key"] = api_key
        response = await litellm.acompletion(**kwargs)
        if response.choices:
            return True, "Connected"
        return False, "No response from provider"
    except litellm.AuthenticationError:
        return False, "Connection failed. Check that your API key is valid and has available credits."
    except litellm.APIConnectionError:
        return False, "Could not reach the LLM provider. Check your network connection."
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


async def parse_shopping_list(
    raw_text: str,
    api_key: str,
    provider: str = "anthropic",
    model: str = "claude-3-haiku-20240307",
    base_url: Optional[str] = None,
) -> list[ParsedListItem]:
    """Parse a raw natural language shopping list into structured items.

    Uses Instructor with LiteLLM to extract items, quantities, units, and notes
    from free-form text (e.g. "a dozen eggs", "2% milk", "that pasta Jen likes").

    When base_url is provided (Ollama), it is forwarded as api_base.

    Returns a list of ParsedListItem objects.
    Raises RuntimeError on LLM or parsing failure.
    """
    try:
        model_str = f"{provider}/{model}" if "/" not in model else model
        client = instructor.from_provider(
            f"litellm/{model_str}",
            async_client=True,
        )

        system_prompt = (
            "You are a shopping list parser. Extract each item from the user's grocery list. "
            "For each item, identify the product name, quantity (default 1), unit if specified, "
            "and any notes (brand preferences, size, style). "
            "Handle natural language like 'a dozen eggs' (quantity=12, name='eggs') "
            "or '2% milk' (name='milk', notes='2% fat')."
        )

        create_kwargs: dict = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text},
            ],
            "response_model": ParsedList,
            "max_tokens": 1000,
            "max_retries": 2,
            "api_key": api_key,
        }
        if base_url:
            create_kwargs["api_base"] = base_url

        result = await client.create(**create_kwargs)
        return result.items
    except Exception as e:
        raise RuntimeError(f"Failed to parse shopping list: {str(e)}") from e


async def match_products(
    list_items: list[ParsedListItem],
    candidates: dict[str, list[ProductCandidate]],
    api_key: str,
    provider: str = "anthropic",
    model: str = "claude-3-haiku-20240307",
    preferences: Optional[dict] = None,
    base_url: Optional[str] = None,
) -> MatchResult:
    """Select the best Kroger product for each shopping list item using an LLM.

    Takes parsed list items and a dict of Kroger product candidates keyed by
    item name. Returns a MatchResult with per-item selections and confidence scores.

    The preferences parameter is a Phase 3 hook (D-07) — pass None in Phase 2.
    When base_url is provided (Ollama), it is forwarded as api_base.
    Raises RuntimeError on LLM or matching failure.
    """
    try:
        model_str = f"{provider}/{model}" if "/" not in model else model
        client = instructor.from_provider(
            f"litellm/{model_str}",
            async_client=True,
        )

        system_prompt = (
            "You are a grocery product matching assistant. For each item in the shopping list, "
            "select the best matching product from the provided Kroger search results. "
            "Consider brand, size, price, and the user's notes. "
            "Rate your confidence from 0.0 to 1.0 — use 0.8+ only when the match is clearly correct. "
            "For items with ambiguous matches (generic descriptions, multiple plausible options), "
            "rate confidence below 0.8. "
            "Always provide 2-4 alternative UPCs when available."
        )
        if preferences is not None:
            system_prompt += (
                f"\n\nUser preferences: {json.dumps(preferences)}. "
                "Prefer products matching these preferences."
            )

        user_message = _build_matching_prompt(list_items, candidates)

        create_kwargs: dict = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "response_model": MatchResult,
            "max_tokens": 2000,
            "max_retries": 2,
            "api_key": api_key,
        }
        if base_url:
            create_kwargs["api_base"] = base_url

        result = await client.create(**create_kwargs)
        return result
    except Exception as e:
        raise RuntimeError(f"Product matching failed: {str(e)}") from e


def _build_matching_prompt(
    list_items: list[ParsedListItem],
    candidates: dict[str, list[ProductCandidate]],
) -> str:
    """Build a compact prompt for the product matching LLM call.

    Formats each shopping list item with its Kroger product candidates.
    Omits display-only fields (thumbnail_url) to stay within token budget.
    """
    lines: list[str] = []
    for item in list_items:
        notes_part = f", notes: {item.notes}" if item.notes else ""
        lines.append(f"Item: {item.name} (qty: {item.quantity}{notes_part})")
        lines.append("Candidates:")
        item_candidates = candidates.get(item.name, [])
        if item_candidates:
            for c in item_candidates:
                price = f"${c.price_regular}" if c.price_regular is not None else "N/A"
                lines.append(f"  - UPC: {c.upc} | {c.brand} {c.description} | {c.size} | {price}")
        else:
            lines.append("  (no candidates found)")
        lines.append("")  # blank line between items
    return "\n".join(lines)
