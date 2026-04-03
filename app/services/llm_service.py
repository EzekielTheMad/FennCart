import litellm


async def test_connection(
    api_key: str,
    provider: str = "anthropic",
    model: str = "claude-3-haiku-20240307",
) -> tuple[bool, str]:
    """Test LLM API key by sending a minimal completion request.

    Returns (success: bool, message: str).
    """
    try:
        # Build model string for LiteLLM: provider/model
        model_str = f"{provider}/{model}" if "/" not in model else model
        response = await litellm.acompletion(
            model=model_str,
            messages=[{"role": "user", "content": "ping"}],
            api_key=api_key,
            max_tokens=5,
        )
        if response.choices:
            return True, "Connected"
        return False, "No response from provider"
    except litellm.AuthenticationError:
        return False, "Connection failed. Check that your API key is valid and has available credits."
    except litellm.APIConnectionError:
        return False, "Could not reach the LLM provider. Check your network connection."
    except Exception as e:
        return False, f"Connection failed: {str(e)}"
