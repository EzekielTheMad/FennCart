"""Centralized LLM constants — single source of truth for defaults and model lists."""

import httpx
import litellm

DEFAULT_LLM_PROVIDER = "anthropic"
DEFAULT_LLM_MODEL = "claude-haiku-4-5-20251001"

# Friendly labels and recommendations for models users are likely to pick.
# Models not in this dict get their raw ID as the label.
MODEL_LABELS: dict[str, dict[str, str]] = {
    "anthropic": {
        "claude-haiku-4-5-20251001": "Claude 4.5 Haiku (recommended — fast, cheap)",
        "claude-haiku-4-5": "Claude 4.5 Haiku (latest)",
        "claude-sonnet-4-6": "Claude 4.6 Sonnet (latest)",
        "claude-sonnet-4-5": "Claude 4.5 Sonnet",
        "claude-sonnet-4-5-20250929": "Claude 4.5 Sonnet (2025-09-29)",
        "claude-opus-4-6": "Claude 4.6 Opus (latest, most capable)",
        "claude-opus-4-5": "Claude 4.5 Opus",
        "claude-opus-4-1": "Claude 4.1 Opus",
    },
    "openai": {
        "gpt-4.1-nano": "GPT-4.1 Nano (recommended — fast, cheap)",
        "gpt-4.1-mini": "GPT-4.1 Mini",
        "gpt-4.1": "GPT-4.1",
        "gpt-4o-mini": "GPT-4o Mini",
        "gpt-4o": "GPT-4o",
        "gpt-5": "GPT-5",
        "gpt-5-mini": "GPT-5 Mini",
        "gpt-5-nano": "GPT-5 Nano",
        "o3-mini": "o3 Mini (reasoning)",
        "o4-mini": "o4 Mini (reasoning)",
    },
}

# Models to mark as recommended (sorted to top of dropdown).
RECOMMENDED_MODELS: dict[str, set[str]] = {
    "anthropic": {"claude-haiku-4-5-20251001", "claude-haiku-4-5"},
    "openai": {"gpt-4.1-nano"},
}

# Substrings that indicate a non-chat model (filter these out of dropdowns).
_NON_CHAT_FILTERS = {
    "tts", "transcribe", "realtime", "audio", "embedding", "dall-e",
    "whisper", "search", "deep-research", "image", "video", "moderation",
    "computer-use", "sora", "codex", "container", "babbage", "davinci",
    "ft:", "chat-latest",
}

# Retired/deprecated model prefixes — exclude from dropdowns.
_DEPRECATED_PREFIXES = {
    "claude-3-",       # All Claude 3.x models retired
    "claude-3.5-",     # Old naming scheme
    "claude-3-5-",     # Old naming scheme
    "claude-3-7-",     # Old naming scheme
    "claude-4-",       # Old naming scheme (use claude-*-4-*)
    "gpt-3.5-",        # GPT-3.5 retired
    "gpt-4-",          # Original GPT-4 series retired
    "chatgpt-",        # Internal alias
}

# Exclude dated snapshot versions (e.g., gpt-4o-2024-08-06) — keep only the base ID.
import re
_DATED_SNAPSHOT_RE = re.compile(r"-\d{4}-?\d{2}-?\d{2}$")


def _is_chat_model(model_id: str, provider: str = "") -> bool:
    """Return True if the model is a current, non-deprecated chat model."""
    model_lower = model_id.lower()
    if any(f in model_lower for f in _NON_CHAT_FILTERS):
        return False
    if any(model_id.startswith(p) for p in _DEPRECATED_PREFIXES):
        return False
    if model_id == "gpt-4":
        return False
    # Exclude dated snapshot versions unless they have a friendly label
    labels = MODEL_LABELS.get(provider, {})
    if _DATED_SNAPSHOT_RE.search(model_id) and model_id not in labels:
        return False
    return True


def _get_static_models(provider: str) -> list[dict]:
    """Get chat models from LiteLLM's static registry for a cloud provider."""
    try:
        all_models = litellm.models_by_provider.get(provider, [])
    except Exception:
        return []

    labels = MODEL_LABELS.get(provider, {})
    recommended = RECOMMENDED_MODELS.get(provider, set())
    models = []

    for model_id in all_models:
        if not _is_chat_model(model_id, provider):
            continue
        models.append({
            "id": model_id,
            "label": labels.get(model_id, model_id),
            "recommended": model_id in recommended,
        })

    # Sort: recommended first, then labeled models, then alphabetical
    models.sort(key=lambda m: (not m["recommended"], m["id"] not in labels, m["id"]))
    return models


async def get_models_for_provider(
    provider: str, ollama_base_url: str | None = None
) -> list[dict]:
    """Return available models for a provider.

    For cloud providers (anthropic, openai): uses LiteLLM's static registry
    with deprecated models filtered out and friendly labels.
    For ollama: fetches from the local Ollama API.
    Returns [{"id": str, "label": str, "recommended": bool}].
    """
    if provider == "ollama":
        if not ollama_base_url:
            return []
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{ollama_base_url.rstrip('/')}/api/tags")
                resp.raise_for_status()
                data = resp.json()
            return [
                {"id": m["name"], "label": m["name"], "recommended": False}
                for m in data.get("models", [])
            ]
        except Exception:
            return []

    return _get_static_models(provider)
