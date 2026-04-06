"""Unit tests for PreferenceService: upsert, contradiction detection,
preferences dict builder, CRUD operations, and NL delta application.

All tests use the test_db fixture (function-scoped in-memory SQLite).
No external services are called.
"""
import pytest
from sqlalchemy import select

from app.services.preference_service import PreferenceService
from app.models.preference_entry import PreferenceEntry
from app.schemas.preferences import (
    ReceiptLineItem,
    PreferenceCreateRequest,
    PreferenceUpdateRequest,
    PreferenceDelta,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_item(
    name: str = "Medium Cheddar",
    brand: str = "Tillamook",
    category: str = "cheddar cheese",
    confidence: float = 0.9,
) -> ReceiptLineItem:
    return ReceiptLineItem(
        product_name=name,
        brand=brand,
        product_category=category,
        confidence=confidence,
    )


async def _seed_entry(
    db,
    category: str = "cheddar cheese",
    brand: str = "Tillamook",
    name: str = "Medium Cheddar",
    count: int = 1,
    source: str = "receipt",
) -> PreferenceEntry:
    """Directly insert a PreferenceEntry for test setup."""
    entry = PreferenceEntry(
        product_category=category,
        brand=brand,
        product_name=name,
        purchase_count=count,
        source=source,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


# ---------------------------------------------------------------------------
# Test 1 — upsert: new item creates entry with purchase_count=1
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_upsert_new_item(test_db):
    """First receipt item creates entry with purchase_count=1 and source='receipt'."""
    svc = PreferenceService(test_db)
    item = _make_item()
    entry = await svc.upsert_from_receipt_item(item)
    await test_db.commit()

    assert entry.purchase_count == 1
    assert entry.source == "receipt"
    assert entry.brand == "Tillamook"
    assert entry.product_category == "cheddar cheese"


# ---------------------------------------------------------------------------
# Test 2 — upsert: same item twice increments purchase_count to 2
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_upsert_increment(test_db):
    """Same item seen twice increments purchase_count from 1 to 2."""
    svc = PreferenceService(test_db)
    item = _make_item()

    await svc.upsert_from_receipt_item(item)
    await test_db.commit()
    entry2 = await svc.upsert_from_receipt_item(item)
    await test_db.commit()

    assert entry2.purchase_count == 2


# ---------------------------------------------------------------------------
# Test 3 — upsert: is_one_time=True does not increment existing entry
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_upsert_one_time_no_increment(test_db):
    """is_one_time=True does not increment purchase_count on existing entry."""
    entry = await _seed_entry(test_db, count=1)

    svc = PreferenceService(test_db)
    item = _make_item()
    updated = await svc.upsert_from_receipt_item(item, is_one_time=True)
    await test_db.commit()

    assert updated.purchase_count == 1  # count unchanged


# ---------------------------------------------------------------------------
# Test 4 — detect_contradictions: existing entry count>=2 + different brand triggers
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_detect_contradictions_triggers(test_db):
    """Established preference (count>=2) with different brand triggers a contradiction."""
    # Seed an established Tillamook preference
    await _seed_entry(test_db, category="cheddar cheese", brand="Tillamook", count=2)

    svc = PreferenceService(test_db)
    # New receipt has Kroger cheddar — contradicts established Tillamook
    new_item = _make_item(brand="Kroger", category="cheddar cheese", name="Sharp Cheddar")
    clean_items, contradictions = await svc.detect_contradictions([new_item])

    assert len(contradictions) == 1
    assert contradictions[0].existing_brand == "Tillamook"
    assert contradictions[0].new_brand == "Kroger"
    assert len(clean_items) == 0


# ---------------------------------------------------------------------------
# Test 5 — detect_contradictions: count==1 does NOT trigger contradiction
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_detect_contradictions_no_trigger_low_count(test_db):
    """Existing entry with purchase_count==1 does NOT trigger a contradiction."""
    # Seed a weak preference (count=1)
    await _seed_entry(test_db, category="cheddar cheese", brand="Tillamook", count=1)

    svc = PreferenceService(test_db)
    new_item = _make_item(brand="Kroger", category="cheddar cheese")
    clean_items, contradictions = await svc.detect_contradictions([new_item])

    assert len(contradictions) == 0
    assert len(clean_items) == 1


# ---------------------------------------------------------------------------
# Test 6 — detect_contradictions: empty brand never triggers
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_detect_contradictions_empty_brand_ignored(test_db):
    """Items with brand='' never trigger contradictions even with established preferences."""
    await _seed_entry(test_db, category="cheddar cheese", brand="Tillamook", count=3)

    svc = PreferenceService(test_db)
    no_brand_item = _make_item(brand="", category="cheddar cheese")
    clean_items, contradictions = await svc.detect_contradictions([no_brand_item])

    assert len(contradictions) == 0
    assert len(clean_items) == 1


# ---------------------------------------------------------------------------
# Test 7 — get_preferences_for_matching: returns only count>=2, max 50, ordered by count DESC
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_preferences_for_matching(test_db):
    """Returns only entries with purchase_count>=2, ordered by count DESC, capped at 50."""
    # Seed entries: two weak (count=1), three strong (count=3, 5, 2)
    await _seed_entry(test_db, brand="Weak1", category="cat1", name="Prod1", count=1)
    await _seed_entry(test_db, brand="Weak2", category="cat2", name="Prod2", count=1)
    await _seed_entry(test_db, brand="Strong1", category="cat3", name="Prod3", count=5)
    await _seed_entry(test_db, brand="Strong2", category="cat4", name="Prod4", count=3)
    await _seed_entry(test_db, brand="Strong3", category="cat5", name="Prod5", count=2)

    svc = PreferenceService(test_db)
    prefs = await svc.get_preferences_for_matching()

    entries = prefs["entries"]
    assert len(entries) == 3  # only count>=2
    # First entry should be the strongest (count=5)
    assert entries[0]["brand"] == "Strong1"
    assert entries[0]["strength"] == "strong"  # count >= 3
    assert entries[2]["strength"] == "moderate"  # count == 2


@pytest.mark.anyio
async def test_get_preferences_for_matching_cap_at_50(test_db):
    """get_preferences_for_matching caps results at 50 entries."""
    # Seed 55 established entries
    for i in range(55):
        entry = PreferenceEntry(
            product_category=f"category_{i}",
            brand=f"Brand{i}",
            product_name=f"Product {i}",
            purchase_count=3,  # all established
            source="receipt",
        )
        test_db.add(entry)
    await test_db.commit()

    svc = PreferenceService(test_db)
    prefs = await svc.get_preferences_for_matching()
    assert len(prefs["entries"]) == 50


# ---------------------------------------------------------------------------
# Test 8 — get_preferences_for_matching: empty dict when no established preferences
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_preferences_empty(test_db):
    """Returns {'entries': []} when no established preferences (count>=2) exist."""
    svc = PreferenceService(test_db)
    prefs = await svc.get_preferences_for_matching()
    assert prefs == {"entries": []}


# ---------------------------------------------------------------------------
# Test 9 — list_preferences with query returns filtered results
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_list_preferences_with_query(test_db):
    """Search query filters results by product_name, brand, or category."""
    await _seed_entry(test_db, brand="Tillamook", name="Medium Cheddar", category="cheddar cheese")
    await _seed_entry(test_db, brand="Organic Valley", name="2% Milk", category="milk")

    svc = PreferenceService(test_db)
    results = await svc.list_preferences(query="Tillamook")

    assert len(results) == 1
    assert results[0].brand == "Tillamook"


# ---------------------------------------------------------------------------
# Test 10 — create_preference: manual entry with source="manual"
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_create_preference_manual(test_db):
    """Manually created preference has source='manual' and purchase_count=1."""
    svc = PreferenceService(test_db)
    data = PreferenceCreateRequest(
        product_category="milk",
        brand="Oatly",
        product_name="Oat Milk",
        notes="Preferred for coffee",
    )
    entry = await svc.create_preference(data)
    await test_db.commit()

    assert entry.source == "manual"
    assert entry.purchase_count == 1
    assert entry.brand == "Oatly"
    assert entry.notes == "Preferred for coffee"


# ---------------------------------------------------------------------------
# Test 11 — update_preference: updates fields
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_update_preference(test_db):
    """update_preference updates only non-None fields and refreshes updated_at."""
    entry = await _seed_entry(test_db, brand="OldBrand", category="milk", name="2% Milk")
    original_updated_at = entry.updated_at

    svc = PreferenceService(test_db)
    data = PreferenceUpdateRequest(brand="NewBrand")
    updated = await svc.update_preference(entry.id, data)
    await test_db.commit()

    assert updated is not None
    assert updated.brand == "NewBrand"
    assert updated.product_name == "2% Milk"  # unchanged
    assert updated.updated_at >= original_updated_at


# ---------------------------------------------------------------------------
# Test 12 — delete_preference: returns True and removes entry
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_delete_preference(test_db):
    """delete_preference removes the entry and returns True; False for missing ID."""
    entry = await _seed_entry(test_db)

    svc = PreferenceService(test_db)
    result = await svc.delete_preference(entry.id)
    await test_db.commit()

    assert result is True

    # Verify gone
    check = await test_db.execute(
        select(PreferenceEntry).where(PreferenceEntry.id == entry.id)
    )
    assert check.scalar_one_or_none() is None

    # Deleting non-existent returns False
    assert await svc.delete_preference(99999) is False


# ---------------------------------------------------------------------------
# Test 13 — bulk_delete: deletes multiple entries, returns count
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_bulk_delete(test_db):
    """bulk_delete removes all specified entries and returns the deleted count."""
    e1 = await _seed_entry(test_db, brand="Brand1", category="cat1", name="Prod1")
    e2 = await _seed_entry(test_db, brand="Brand2", category="cat2", name="Prod2")
    e3 = await _seed_entry(test_db, brand="Brand3", category="cat3", name="Prod3")

    svc = PreferenceService(test_db)
    count = await svc.bulk_delete([e1.id, e2.id])
    await test_db.commit()

    assert count == 2

    # e3 should still exist
    remaining = await svc.list_preferences()
    assert len(remaining) == 1
    assert remaining[0].id == e3.id


# ---------------------------------------------------------------------------
# Test 14 — apply_nl_delta: action="add" creates new entry with source="nl_chat"
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_apply_nl_delta_add(test_db):
    """action='add' creates a new PreferenceEntry with source='nl_chat'."""
    svc = PreferenceService(test_db)
    delta = PreferenceDelta(
        action="add",
        category="milk",
        new_brand="Oatly",
        product_name="Oat Milk",
        human_summary="Add Oatly Oat Milk as a preference",
    )
    entry = await svc.apply_nl_delta(delta)
    await test_db.commit()

    assert entry is not None
    assert entry.source == "nl_chat"
    assert entry.brand == "Oatly"
    assert entry.product_category == "milk"


# ---------------------------------------------------------------------------
# Test 15 — apply_nl_delta: action="remove" deletes matching entry
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_apply_nl_delta_remove(test_db):
    """action='remove' deletes the matching entry and returns None."""
    await _seed_entry(test_db, category="milk", brand="Kroger", name="2% Milk")

    svc = PreferenceService(test_db)
    delta = PreferenceDelta(
        action="remove",
        category="milk",
        old_brand="Kroger",
        human_summary="Remove Kroger milk preference",
    )
    result = await svc.apply_nl_delta(delta)
    await test_db.commit()

    assert result is None

    # Verify entry is gone
    check = await test_db.execute(
        select(PreferenceEntry).where(
            PreferenceEntry.product_category == "milk",
            PreferenceEntry.brand == "Kroger",
        )
    )
    assert check.scalar_one_or_none() is None


# ---------------------------------------------------------------------------
# Test 16 — apply_nl_delta: action="replace" updates brand on existing entry
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_apply_nl_delta_replace(test_db):
    """action='replace' changes the brand on an existing entry and sets source='nl_chat'."""
    await _seed_entry(test_db, category="milk", brand="Kroger", name="Whole Milk", count=3)

    svc = PreferenceService(test_db)
    delta = PreferenceDelta(
        action="replace",
        category="milk",
        old_brand="Kroger",
        new_brand="Organic Valley",
        human_summary="Switch from Kroger to Organic Valley milk",
    )
    updated = await svc.apply_nl_delta(delta)
    await test_db.commit()

    assert updated is not None
    assert updated.brand == "Organic Valley"
    assert updated.source == "nl_chat"
    # purchase_count should be preserved
    assert updated.purchase_count == 3
