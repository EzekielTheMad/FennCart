"""Centralized LLM constants — single source of truth for defaults and model lists."""

import httpx
import litellm

DEFAULT_LLM_PROVIDER = "anthropic"
DEFAULT_LLM_MODEL = "claude-haiku-4-5-20251001"

# Models to highlight with a recommendation label.
# Only recommended models need entries — others get their ID as the label.
RECOMMENDED_MODELS: dict[str, dict[str, str]] = {
    "anthropic": {
        "claude-haiku-4-5-20251001": "Claude 4.5 Haiku — recommended (fast, cheap, structured output)",
    },
    "openai": {
        "gpt-4.1-nano": "GPT-4.1 Nano — recommended (fast, cheap)",
    },
}

# Substrings that indicate a non-chat model (filter these out of dropdowns).
_NON_CHAT_FILTERS = {
    "tts", "transcribe", "realtime", "audio", "embedding", "dall-e",
    "whisper", "search", "deep-research", "image", "video", "moderation",
    "computer-use",
}


def _is_chat_model(model_id: str) -> bool:
    """Return True if the model is likely a chat/completion model."""
    model_lower = model_id.lower()
    return not any(f in model_lower for f in _NON_CHAT_FILTERS)


def _get_static_models(provider: str) -> list[dict]:
    """Get chat models from LiteLLM's static registry for a cloud provider."""
    try:
        all_models = litellm.models_by_provider.get(provider, [])
    except Exception:
        return []

    recommendations = RECOMMENDED_MODELS.get(provider, {})
    models = []

    for model_id in all_models:
        if not _is_chat_model(model_id):
            continue
        rec_label = recommendations.get(model_id)
        models.append({
            "id": model_id,
            "label": rec_label or model_id,
            "recommended": model_id in recommendations,
        })

    # Sort: recommended first, then alphabetical
    models.sort(key=lambda m: (not m["recommended"], m["id"]))
    return models


async def get_models_for_provider(
    provider: str, ollama_base_url: str | None = None
) -> list[dict]:
    """Return available models for a provider.

    For cloud providers (anthropic, openai): uses LiteLLM's static registry.
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
