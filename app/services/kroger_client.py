import httpx
from typing import Optional

KROGER_BASE = "https://api.kroger.com/v1"


async def search_products(
    term: str,
    location_id: str,
    client_id: str,
    client_secret: str,
    limit: int = 10,
) -> list[dict]:
    """Search Kroger Products API for curbside-eligible products.

    Returns raw product dicts from Kroger API (data array).
    DO NOT persist results — TOS prohibits storing search data.

    Raises RuntimeError on authentication failure or HTTP errors.
    """
    success, msg, app_token = await get_app_token(client_id, client_secret)
    if not success or app_token is None:
        raise RuntimeError(msg)

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{KROGER_BASE}/products",
                params={
                    "filter.term": term,
                    "filter.locationId": location_id,
                    "filter.fulfillment": "csp",  # curbside pickup — must be lowercase 'csp'
                    "filter.limit": limit,
                },
                headers={"Authorization": f"Bearer {app_token}"},
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json().get("data", [])
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Kroger product search failed: {e.response.status_code}")
    except httpx.ConnectError:
        raise RuntimeError("Could not reach Kroger API")


async def add_to_cart(
    items: list[dict],
    access_token: str,
) -> tuple[bool, str]:
    """Add items to the user's Kroger cart via the Cart API.

    items: list of dicts with keys 'upc' and 'quantity'.
    access_token: user OAuth token (NOT client credentials token).

    Returns (success: bool, message: str).
    Success response from Kroger is 204 No Content — do NOT parse body.
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{KROGER_BASE}/cart/add",
                json={"items": items},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                timeout=15.0,
            )
            if resp.status_code == 204:
                return (True, "Items added")
            if resp.status_code == 200:
                return (True, "Items added")
            if resp.status_code == 401:
                return (False, "Kroger session expired. Please re-authenticate.")
            return (False, f"Cart add failed: {resp.status_code}")
    except httpx.ConnectError:
        return (False, "Could not reach Kroger API")


async def get_app_token(
    client_id: str, client_secret: str
) -> tuple[bool, str, Optional[str]]:
    """Get a client credentials token from Kroger API.

    Returns (success: bool, message: str, token: Optional[str]).
    Used to validate Kroger developer credentials in wizard step 2,
    and for store location search in step 3.
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{KROGER_BASE}/connect/oauth2/token",
                data={"grant_type": "client_credentials", "scope": "product.compact"},
                auth=(client_id, client_secret),
                timeout=10.0,
            )
            if resp.status_code == 401:
                return (
                    False,
                    "Kroger rejected these credentials. Double-check your Client ID and Client Secret at developer.kroger.com.",
                    None,
                )
            resp.raise_for_status()
            token = resp.json()["access_token"]
            return True, "Credentials accepted", token
    except httpx.ConnectError:
        return False, "Could not reach Kroger API. Check your network connection.", None
    except httpx.HTTPStatusError as e:
        return False, f"Kroger API error: {e.response.status_code}", None
    except Exception as e:
        return False, f"Credential validation failed: {str(e)}", None


async def search_stores_by_zip(
    zip_code: str, app_token: str
) -> tuple[bool, str, list[dict]]:
    """Search for Kroger/Fry's stores near a zip code.

    Returns (success: bool, message: str, stores: list[dict]).
    Each store dict has keys: locationId, name, address.
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{KROGER_BASE}/locations",
                params={
                    "filter.zipCode.near": zip_code,
                    "filter.limit": 10,
                    "filter.chain": "Fry's",
                },
                headers={"Authorization": f"Bearer {app_token}"},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])
            stores = []
            for loc in data:
                addr = loc.get("address", {})
                stores.append(
                    {
                        "locationId": loc.get("locationId", ""),
                        "name": loc.get("name", "Unknown"),
                        "address": f"{addr.get('addressLine1', '')}, {addr.get('city', '')}",
                    }
                )
            if not stores:
                return (
                    True,
                    "No Fry's stores found near that zip code. Try a nearby zip code.",
                    [],
                )
            return True, f"Found {len(stores)} stores", stores
    except Exception as e:
        return False, f"Store search failed: {str(e)}", []
