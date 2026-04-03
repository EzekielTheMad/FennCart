"""Tests for the Kroger API client service."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.kroger_client import get_app_token, search_stores_by_zip


@pytest.mark.anyio
@patch("app.services.kroger_client.httpx.AsyncClient")
async def test_get_app_token_success(mock_client_class):
    """Client credentials grant returns token on valid credentials."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token": "test_token"}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_class.return_value = mock_client

    success, msg, token = await get_app_token("id", "secret")
    assert success is True
    assert token == "test_token"


@pytest.mark.anyio
@patch("app.services.kroger_client.httpx.AsyncClient")
async def test_get_app_token_invalid_creds(mock_client_class):
    """Client credentials grant returns error on 401."""
    mock_response = MagicMock()
    mock_response.status_code = 401

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_class.return_value = mock_client

    success, msg, token = await get_app_token("bad_id", "bad_secret")
    assert success is False
    assert "rejected" in msg.lower()
    assert token is None


@pytest.mark.anyio
@patch("app.services.kroger_client.httpx.AsyncClient")
async def test_search_stores_returns_formatted(mock_client_class):
    """Store search returns formatted store list."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "locationId": "123",
                "name": "Fry's Marketplace",
                "address": {"addressLine1": "123 Main St", "city": "Phoenix"},
            },
        ]
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_class.return_value = mock_client

    success, msg, stores = await search_stores_by_zip("85001", "token")
    assert success is True
    assert len(stores) == 1
    assert stores[0]["locationId"] == "123"
    assert "Fry's Marketplace" in stores[0]["name"]
