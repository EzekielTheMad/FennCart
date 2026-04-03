"""Tests for Kroger product search and cart add functions."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.kroger_client import search_products, add_to_cart


def _make_mock_client(method: str, response: MagicMock) -> MagicMock:
    """Helper: build a mocked AsyncClient context manager with the given response."""
    mock_client = AsyncMock()
    getattr(mock_client, method).return_value = response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    return mock_client


def _make_ok_token_response() -> MagicMock:
    """Mock response for get_app_token POST call (200 + access_token)."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"access_token": "app_token_xyz"}
    resp.raise_for_status = MagicMock()
    return resp


@pytest.mark.anyio
@patch("app.services.kroger_client.httpx.AsyncClient")
async def test_search_products_uses_csp_filter(mock_client_class):
    """search_products must pass filter.fulfillment=csp in the GET request params."""
    # First call: get_app_token POST; Second call: products GET
    token_resp = _make_ok_token_response()

    product_resp = MagicMock()
    product_resp.status_code = 200
    product_resp.json.return_value = {"data": []}
    product_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = token_resp
    mock_client.get.return_value = product_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_class.return_value = mock_client

    await search_products("milk", "12345", "id", "secret")

    # Assert GET was called with csp filter
    get_call = mock_client.get.call_args
    assert get_call is not None
    params = get_call.kwargs.get("params", {})
    assert params.get("filter.fulfillment") == "csp", (
        f"Expected filter.fulfillment='csp', got {params.get('filter.fulfillment')!r}"
    )


@pytest.mark.anyio
@patch("app.services.kroger_client.httpx.AsyncClient")
async def test_search_products_returns_data(mock_client_class):
    """search_products returns the data array from the Kroger API response."""
    token_resp = _make_ok_token_response()

    product_data = [
        {"upc": "0001234567890", "description": "Kroger Whole Milk", "brand": "Kroger"},
        {"upc": "0009876543210", "description": "Organic Valley Whole Milk", "brand": "Organic Valley"},
    ]
    product_resp = MagicMock()
    product_resp.status_code = 200
    product_resp.json.return_value = {"data": product_data}
    product_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = token_resp
    mock_client.get.return_value = product_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_class.return_value = mock_client

    result = await search_products("milk", "12345", "id", "secret")

    assert result == product_data
    assert len(result) == 2
    assert result[0]["upc"] == "0001234567890"


@pytest.mark.anyio
@patch("app.services.kroger_client.httpx.AsyncClient")
async def test_search_products_handles_error(mock_client_class):
    """search_products raises RuntimeError on HTTP 500 from products endpoint."""
    token_resp = _make_ok_token_response()

    error_resp = MagicMock()
    error_resp.status_code = 500
    http_error = Exception()
    error_resp.raise_for_status.side_effect = _make_http_status_error(500, error_resp)

    mock_client = AsyncMock()
    mock_client.post.return_value = token_resp
    mock_client.get.return_value = error_resp
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_class.return_value = mock_client

    with pytest.raises(RuntimeError, match="500"):
        await search_products("milk", "12345", "id", "secret")


def _make_http_status_error(status_code: int, response: MagicMock):
    """Create an httpx.HTTPStatusError with the given status code."""
    import httpx
    request = httpx.Request("GET", "https://api.kroger.com/v1/products")
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = status_code
    return httpx.HTTPStatusError(
        f"{status_code} Error",
        request=request,
        response=mock_response,
    )


@pytest.mark.anyio
@patch("app.services.kroger_client.httpx.AsyncClient")
async def test_add_to_cart_success_204(mock_client_class):
    """add_to_cart returns (True, 'Items added') on 204 No Content response."""
    mock_response = MagicMock()
    mock_response.status_code = 204

    mock_client = _make_mock_client("put", mock_response)
    mock_client_class.return_value = mock_client

    success, msg = await add_to_cart(
        [{"upc": "0001234567890", "quantity": 1}],
        access_token="user_oauth_token",
    )
    assert success is True
    assert msg == "Items added"


@pytest.mark.anyio
@patch("app.services.kroger_client.httpx.AsyncClient")
async def test_add_to_cart_expired_token_401(mock_client_class):
    """add_to_cart returns (False, ...) with 'expired' message on 401 Unauthorized."""
    mock_response = MagicMock()
    mock_response.status_code = 401

    mock_client = _make_mock_client("put", mock_response)
    mock_client_class.return_value = mock_client

    success, msg = await add_to_cart(
        [{"upc": "0001234567890", "quantity": 2}],
        access_token="expired_token",
    )
    assert success is False
    assert "expired" in msg.lower()


@pytest.mark.anyio
@patch("app.services.kroger_client.httpx.AsyncClient")
async def test_add_to_cart_uses_put_method(mock_client_class):
    """add_to_cart must use HTTP PUT (not POST) to the cart/add endpoint."""
    mock_response = MagicMock()
    mock_response.status_code = 204

    mock_client = _make_mock_client("put", mock_response)
    mock_client_class.return_value = mock_client

    await add_to_cart(
        [{"upc": "0001234567890", "quantity": 1}],
        access_token="user_oauth_token",
    )

    # Verify PUT was called (not GET/POST)
    mock_client.put.assert_called_once()
    put_call = mock_client.put.call_args
    url = put_call.args[0] if put_call.args else put_call.kwargs.get("url", "")
    assert "cart/add" in url, f"Expected URL containing 'cart/add', got: {url!r}"
    # Also verify POST was NOT called
    mock_client.post.assert_not_called()
