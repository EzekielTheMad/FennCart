import httpx
from typing import Optional

KROGER_BASE = "https://api.kroger.com/v1"


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
