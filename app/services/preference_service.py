"""PreferenceService: CRUD, contradiction detection, and preference dict builder for the preference system."""
from typing import Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete as sa_delete

from app.models.preference_entry import PreferenceEntry
from app.schemas.preferences import (
    ReceiptLineItem,
    ContradictionCandidate,
    PreferenceCreateRequest,
    PreferenceUpdateRequest,
    PreferenceDelta,
)


class PreferenceService:
    """Service layer for preference profile management.

    Preference signals come ONLY from user-uploaded receipts and manual entries.
    Never from cart_items or Kroger API responses (TOS).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_from_receipt_item(
        self, item: ReceiptLineItem, is_one_time: bool = False
    ) -> PreferenceEntry:
        """Upsert a PreferenceEntry from a parsed receipt line item.

        If an entry already exists for (product_category, brand, product_name):
        - is_one_time=False: increment purchase_count and update timestamps
        - is_one_time=True: do not increment (user chose one-time substitution at D-06)

        If no entry exists: create one with purchase_count=1 and source="receipt".
        """
        result = await self.db.execute(
            select(PreferenceEntry).where(
                and_(
                    PreferenceEntry.product_category == item.product_category,
                    PreferenceEntry.brand == item.brand,
                    PreferenceEntry.product_name == item.product_name,
                )
            )
        )
        entry = result.scalar_one_or_none()

        if entry is not None:
            if not is_one_time:
                entry.purchase_count += 1
                entry.last_seen_at = datetime.utcnow()
                entry.updated_at = datetime.utcnow()
        else:
            entry = PreferenceEntry(
                product_category=item.product_category,
                brand=item.brand,
                product_name=item.product_name,
                purchase_count=1,
                source="receipt",
                last_seen_at=datetime.utcnow(),
                first_seen_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

        self.db.add(entry)
        await self.db.flush()
        return entry

    async def detect_contradictions(
        self, items: list[ReceiptLineItem]
    ) -> tuple[list[ReceiptLineItem], list[ContradictionCandidate]]:
        """Detect brand contradictions between parsed receipt items and existing preferences.

        A contradiction occurs when a receipt item has a non-empty brand that differs
        from an established preference (purchase_count >= 2) in the same product_category.

        Returns (clean_items, contradictions) where clean_items are those without contradictions.
        Items with empty brand ("") never trigger contradictions.
        """
        clean_items: list[ReceiptLineItem] = []
        contradictions: list[ContradictionCandidate] = []

        for index, item in enumerate(items):
            if not item.brand:
                clean_items.append(item)
                continue

            result = await self.db.execute(
                select(PreferenceEntry).where(
                    and_(
                        PreferenceEntry.product_category == item.product_category,
                        PreferenceEntry.brand != item.brand,
                        PreferenceEntry.purchase_count >= 2,
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing is not None:
                contradictions.append(
                    ContradictionCandidate(
                        category=item.product_category,
                        existing_brand=existing.brand,
                        existing_count=existing.purchase_count,
                        new_brand=item.brand,
                        product_name=item.product_name,
                        new_item_index=index,
                    )
                )
            else:
                clean_items.append(item)

        return clean_items, contradictions

    async def get_preferences_for_matching(self) -> dict:
        """Build a preferences dict for LLM product matching.

        Returns entries with purchase_count >= 2, ordered by strength descending,
        limited to 50 entries for token budget.

        Preference signals come ONLY from user-uploaded receipts and manual entries.
        Never from cart_items or Kroger API responses (TOS).
        """
        result = await self.db.execute(
            select(PreferenceEntry)
            .where(PreferenceEntry.purchase_count >= 2)
            .order_by(
                PreferenceEntry.purchase_count.desc(),
                PreferenceEntry.last_seen_at.desc(),
            )
            .limit(50)
        )
        entries = result.scalars().all()

        if not entries:
            return {"entries": []}

        return {
            "entries": [
                {
                    "category": e.product_category,
                    "brand": e.brand,
                    "product": e.product_name,
                    "strength": "strong" if e.purchase_count >= 3 else "moderate",
                }
                for e in entries
            ]
        }

    async def list_preferences(self, query: Optional[str] = None) -> list[PreferenceEntry]:
        """List all preferences, optionally filtered by a search query.

        Query is matched case-insensitively against product_name, brand, and product_category.
        Results ordered by purchase_count DESC, updated_at DESC.
        """
        stmt = select(PreferenceEntry)
        if query:
            stmt = stmt.where(
                or_(
                    PreferenceEntry.product_name.ilike(f"%{query}%"),
                    PreferenceEntry.brand.ilike(f"%{query}%"),
                    PreferenceEntry.product_category.ilike(f"%{query}%"),
                )
            )
        stmt = stmt.order_by(
            PreferenceEntry.purchase_count.desc(),
            PreferenceEntry.updated_at.desc(),
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_preference(self, pref_id: int) -> Optional[PreferenceEntry]:
        """Retrieve a single preference by ID."""
        result = await self.db.execute(
            select(PreferenceEntry).where(PreferenceEntry.id == pref_id)
        )
        return result.scalar_one_or_none()

    async def create_preference(self, data: PreferenceCreateRequest) -> PreferenceEntry:
        """Create a new preference entry from a manual request."""
        entry = PreferenceEntry(
            product_category=data.product_category,
            brand=data.brand,
            product_name=data.product_name,
            notes=data.notes,
            source="manual",
            purchase_count=1,
            last_seen_at=datetime.utcnow(),
            first_seen_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def update_preference(
        self, pref_id: int, data: PreferenceUpdateRequest
    ) -> Optional[PreferenceEntry]:
        """Update an existing preference entry. Only non-None fields are updated."""
        entry = await self.get_preference(pref_id)
        if entry is None:
            return None

        if data.product_name is not None:
            entry.product_name = data.product_name
        if data.brand is not None:
            entry.brand = data.brand
        if data.product_category is not None:
            entry.product_category = data.product_category
        if data.notes is not None:
            entry.notes = data.notes

        entry.updated_at = datetime.utcnow()
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def delete_preference(self, pref_id: int) -> bool:
        """Delete a preference by ID. Returns True if found and deleted, False if not found."""
        entry = await self.get_preference(pref_id)
        if entry is None:
            return False
        await self.db.delete(entry)
        await self.db.flush()
        return True

    async def bulk_delete(self, ids: list[int]) -> int:
        """Delete all preference entries with IDs in the given list.

        Returns the count of deleted entries.
        """
        result = await self.db.execute(
            sa_delete(PreferenceEntry).where(PreferenceEntry.id.in_(ids))
        )
        await self.db.flush()
        return result.rowcount

    async def apply_nl_delta(self, delta: PreferenceDelta) -> Optional[PreferenceEntry]:
        """Apply a structured natural language preference delta to the preference store.

        Handles: "add", "remove", "replace". "clarify" should never reach this method
        (handled in the router before calling apply_nl_delta).
        """
        if delta.action == "add":
            entry = PreferenceEntry(
                product_category=delta.category,
                brand=delta.new_brand or "",
                product_name=delta.product_name or delta.category,
                source="nl_chat",
                purchase_count=1,
                last_seen_at=datetime.utcnow(),
                first_seen_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(entry)
            await self.db.flush()
            return entry

        elif delta.action == "remove":
            result = await self.db.execute(
                select(PreferenceEntry).where(
                    and_(
                        PreferenceEntry.product_category == delta.category,
                        PreferenceEntry.brand == delta.old_brand,
                    )
                )
            )
            entry = result.scalar_one_or_none()
            if entry is not None:
                await self.db.delete(entry)
                await self.db.flush()
            return None

        elif delta.action == "replace":
            result = await self.db.execute(
                select(PreferenceEntry).where(
                    and_(
                        PreferenceEntry.product_category == delta.category,
                        PreferenceEntry.brand == delta.old_brand,
                    )
                )
            )
            entry = result.scalar_one_or_none()
            if entry is not None:
                entry.brand = delta.new_brand or ""
                entry.source = "nl_chat"
                entry.updated_at = datetime.utcnow()
                self.db.add(entry)
                await self.db.flush()
            return entry

        # "clarify" and unknown actions should not reach here
        return None
