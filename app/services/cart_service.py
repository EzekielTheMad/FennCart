"""CartService: orchestrates the full parse -> search -> match -> add pipeline."""
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.shopping import (
    ParsedListItem,
    ProductCandidate,
    ItemMatch,
    MatchResult,
    ConfirmedItem,
)
from app.models.cart_session import CartSession
from app.models.cart_item import CartItem
from app.services.kroger_client import search_products, add_to_cart
from app.services.llm_service import parse_shopping_list, match_products


class CartService:
    """Orchestrates the shopping list -> Kroger cart pipeline.

    Flow: parse raw text -> search Kroger for each item -> LLM match ->
    partition by confidence -> confirm selections -> add to cart & persist.
    """

    def __init__(
        self,
        db: AsyncSession,
        location_id: str,
        kroger_client_id: str,
        kroger_client_secret: str,
        llm_api_key: str,
        llm_provider: str = "anthropic",
        llm_model: str = "claude-haiku-4-5-20251001",
        llm_ollama_base_url: Optional[str] = None,
    ):
        self.db = db
        self.location_id = location_id
        self.kroger_client_id = kroger_client_id
        self.kroger_client_secret = kroger_client_secret
        self.llm_api_key = llm_api_key
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.llm_ollama_base_url = llm_ollama_base_url
        # In-memory dedup cache keyed by item.name.lower().strip() (Pitfall 7 — TOS-safe, not persistent)
        self._search_cache: dict[str, list[dict]] = {}
        # Tracks whether preferences were loaded and passed to match_products (Phase 3)
        self._preferences_loaded: bool = False

    async def process_list(
        self,
        raw_text: str,
        preferences: Optional[dict] = None,
    ) -> tuple[MatchResult, dict[str, list[ProductCandidate]]]:
        """Parse raw shopping list text, search Kroger, and LLM-match products.

        Returns (match_result, candidates_dict) where candidates_dict maps each
        item name to its ProductCandidate list for use in swap dropdowns.
        """
        # Step 1: parse natural language into structured items
        parsed_items: list[ParsedListItem] = await parse_shopping_list(
            raw_text,
            self.llm_api_key,
            self.llm_provider,
            self.llm_model,
            base_url=self.llm_ollama_base_url,
        )

        # Step 2: search Kroger for each item, deduplicating within session
        candidates_dict: dict[str, list[ProductCandidate]] = {}
        for item in parsed_items:
            cache_key = item.name.lower().strip()
            if cache_key not in self._search_cache:
                raw_products = await search_products(
                    item.name,
                    self.location_id,
                    self.kroger_client_id,
                    self.kroger_client_secret,
                    limit=10,
                )
                self._search_cache[cache_key] = raw_products
            candidates = [
                self._to_candidate(p) for p in self._search_cache[cache_key]
            ]
            candidates_dict[item.name] = candidates

        # Step 2.5: Auto-load preferences if not provided (Phase 3 integration)
        if preferences is None:
            from app.services.preference_service import PreferenceService
            pref_service = PreferenceService(self.db)
            loaded_prefs = await pref_service.get_preferences_for_matching()
            if loaded_prefs["entries"]:
                preferences = loaded_prefs
                # Flag for template context — indicates preferences influenced matching
                self._preferences_loaded = True
            else:
                self._preferences_loaded = False
        else:
            self._preferences_loaded = True

        # Step 3: LLM match — select best product per item with confidence scores
        match_result: MatchResult = await match_products(
            parsed_items,
            candidates_dict,
            self.llm_api_key,
            self.llm_provider,
            self.llm_model,
            preferences=preferences,
            base_url=self.llm_ollama_base_url,
        )

        return (match_result, candidates_dict)

    @property
    def preferences_loaded(self) -> bool:
        """True if preferences were loaded and passed to match_products in the last process_list call."""
        return self._preferences_loaded

    def partition_matches(
        self,
        match_result: MatchResult,
    ) -> tuple[list[ItemMatch], list[ItemMatch]]:
        """Split matches into review items (low confidence) and auto items (high confidence).

        Threshold: confidence >= 0.8 -> auto-matched (SRCH-04).
        Returns (review_items, auto_items).
        """
        review_items: list[ItemMatch] = []
        auto_items: list[ItemMatch] = []
        for match in match_result.matches:
            if match.confidence < 0.8:
                review_items.append(match)
            else:
                auto_items.append(match)
        return (review_items, auto_items)

    async def add_confirmed_to_cart(
        self,
        confirmed_items: list[ConfirmedItem],
        access_token: str,
    ) -> tuple[CartSession, int, int, str]:
        """Add confirmed items to Kroger cart and persist a local session record.

        Persists CartItems to SQLite regardless of Kroger API outcome so the
        user has a local record.

        Returns (session, success_count, fail_count, error_message).
        """
        # Step 1: calculate estimated total using price field from ConfirmedItem
        estimated_total = sum(
            (item.price or 0) * item.quantity
            for item in confirmed_items
            if item.price is not None
        )

        # Step 2: create CartSession record
        session_record = CartSession(
            created_at=datetime.utcnow(),
            item_count=len(confirmed_items),
            estimated_total=estimated_total if estimated_total > 0 else None,
        )
        self.db.add(session_record)
        await self.db.flush()  # flush to get generated ID

        # Step 3: build Kroger cart payload
        cart_payload = [
            {"upc": item.upc, "quantity": item.quantity}
            for item in confirmed_items
        ]

        # Step 4: call Kroger Cart API
        success, error_message = await add_to_cart(cart_payload, access_token)

        # Step 5: persist CartItems to local DB regardless of Kroger outcome
        for item in confirmed_items:
            cart_item = CartItem(
                session_id=session_record.id,
                upc=item.upc,
                description=item.description,
                brand=item.brand or None,
                size=item.size or None,
                quantity=item.quantity,
                price_regular=item.price,
                price_promo=None,
                added_at=datetime.utcnow(),
            )
            self.db.add(cart_item)

        await self.db.commit()
        await self.db.refresh(session_record)

        if success:
            return (session_record, len(confirmed_items), 0, "")
        else:
            return (session_record, 0, len(confirmed_items), error_message)

    async def get_session_items(
        self,
        session_id: int,
    ) -> tuple[Optional[CartSession], list[CartItem]]:
        """Retrieve a CartSession and its associated CartItems by session ID."""
        session_result = await self.db.execute(
            select(CartSession).where(CartSession.id == session_id)
        )
        session_record = session_result.scalar_one_or_none()

        items_result = await self.db.execute(
            select(CartItem).where(CartItem.session_id == session_id)
        )
        items = list(items_result.scalars().all())

        return (session_record, items)

    @staticmethod
    def _to_candidate(product_dict: dict) -> ProductCandidate:
        """Convert a raw Kroger product dict to a ProductCandidate.

        Defensive: uses .get() throughout; handles missing nested fields gracefully.
        """
        items_list = product_dict.get("items", [])
        first_item = items_list[0] if items_list else {}

        # Extract price from first item
        price_info = first_item.get("price", {}) or {}
        price_regular: Optional[float] = price_info.get("regular")
        price_promo: Optional[float] = price_info.get("promo")

        # Extract size from first item
        size: str = first_item.get("size", "")

        # Extract thumbnail: first image with perspective "front", first size "thumbnail"
        thumbnail_url: Optional[str] = None
        images = product_dict.get("images", [])
        for img in images:
            if img.get("perspective") == "front":
                for sz in img.get("sizes", []):
                    if sz.get("size") == "thumbnail":
                        thumbnail_url = sz.get("url")
                        break
                if thumbnail_url:
                    break

        return ProductCandidate(
            upc=product_dict.get("productId", ""),
            description=product_dict.get("description", ""),
            brand=product_dict.get("brand", ""),
            size=size,
            price_regular=price_regular,
            price_promo=price_promo,
            thumbnail_url=thumbnail_url,
        )
