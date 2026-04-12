"""Preferences router: all /preferences/* endpoints for the preference management UI."""
import json
from typing import Optional

import instructor

from fastapi import APIRouter, Request, Depends, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.config import get_settings
from app.services.llm_config import get_active_llm_config
from app.services.preference_service import PreferenceService
from app.services.receipt_parser import extract_receipt_text, parse_receipt_with_llm
from app.schemas.preferences import (
    PreferenceCreateRequest,
    PreferenceUpdateRequest,
    ReceiptLineItem,
    ContradictionCandidate,
    PreferenceDelta,
)
from app.models.receipt_upload import ReceiptUpload

templates = Jinja2Templates(directory="templates")

router = APIRouter(prefix="/preferences", tags=["preferences"])


# ---------------------------------------------------------------------------
# Preference CRUD endpoints
# ---------------------------------------------------------------------------


@router.get("/list", response_class=HTMLResponse)
async def preference_list(
    request: Request,
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_session),
):
    """HTMX partial: searchable preference list.

    Query param: q (optional search string).
    Target: #pref-list-container, triggered by search input 300ms debounce.
    """
    entries = await PreferenceService(db).list_preferences(query=q)
    return templates.TemplateResponse(
        request,
        "partials/pref_list.html",
        {"preferences": entries, "query": q},
    )


@router.get("/{pref_id}/row", response_class=HTMLResponse)
async def preference_row(
    request: Request,
    pref_id: int,
    db: AsyncSession = Depends(get_session),
):
    """HTMX partial: single preference display row.

    Used for: cancel inline edit, after save.
    """
    entry = await PreferenceService(db).get_preference(pref_id)
    return templates.TemplateResponse(
        request,
        "partials/pref_row.html",
        {"pref": entry},
    )


@router.get("/{pref_id}/edit-form", response_class=HTMLResponse)
async def preference_edit_form(
    request: Request,
    pref_id: int,
    db: AsyncSession = Depends(get_session),
):
    """HTMX partial: inline edit form that replaces a preference row."""
    entry = await PreferenceService(db).get_preference(pref_id)
    return templates.TemplateResponse(
        request,
        "partials/pref_edit_form.html",
        {"pref": entry},
    )


@router.put("/{pref_id}", response_class=HTMLResponse)
async def preference_update(
    request: Request,
    pref_id: int,
    product_name: str = Form(...),
    brand: str = Form(...),
    product_category: str = Form(...),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_session),
):
    """Update a preference entry and return the updated display row."""
    data = PreferenceUpdateRequest(
        product_name=product_name,
        brand=brand,
        product_category=product_category,
        notes=notes if notes else None,
    )
    entry = await PreferenceService(db).update_preference(pref_id, data)
    await db.commit()
    return templates.TemplateResponse(
        request,
        "partials/pref_row.html",
        {"pref": entry},
    )


@router.post("/create", response_class=HTMLResponse)
async def preference_create(
    request: Request,
    product_name: str = Form(...),
    brand: str = Form(...),
    product_category: str = Form(...),
    notes: str = Form(""),
    db: AsyncSession = Depends(get_session),
):
    """Add a new preference entry and return the display row.

    HTMX target: prepend to list container.
    """
    data = PreferenceCreateRequest(
        product_category=product_category,
        brand=brand,
        product_name=product_name,
        notes=notes if notes else None,
    )
    entry = await PreferenceService(db).create_preference(data)
    await db.commit()
    return templates.TemplateResponse(
        request,
        "partials/pref_row.html",
        {"pref": entry},
    )


@router.delete("/{pref_id}", response_class=HTMLResponse)
async def preference_delete(
    pref_id: int,
    db: AsyncSession = Depends(get_session),
):
    """Delete a single preference entry.

    Returns empty string — HTMX removes the row via hx-swap="outerHTML".
    """
    await PreferenceService(db).delete_preference(pref_id)
    await db.commit()
    return HTMLResponse("")


@router.post("/bulk-delete", response_class=HTMLResponse)
async def preference_bulk_delete(
    request: Request,
    ids: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    """Bulk delete preferences by comma-separated ID list.

    Returns a refreshed preference list partial.
    """
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    await PreferenceService(db).bulk_delete(id_list)
    await db.commit()
    entries = await PreferenceService(db).list_preferences()
    return templates.TemplateResponse(
        request,
        "partials/pref_list.html",
        {"preferences": entries, "query": None},
    )


# ---------------------------------------------------------------------------
# Receipt upload and review endpoints
# ---------------------------------------------------------------------------


@router.get("/upload-form", response_class=HTMLResponse)
async def upload_form(request: Request):
    """Return the receipt upload form partial (for 'Try another receipt' button)."""
    return templates.TemplateResponse(request, "partials/receipt_upload_form.html")


@router.post("/upload", response_class=HTMLResponse)
async def upload_receipt(
    request: Request,
    receipt_pdfs: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_session),
):
    """Upload one or more receipt PDFs, extract text, parse with LLM, detect contradictions.

    Processes files sequentially, merging all items and warnings.
    Stores parsed items and contradictions in server-side session.
    Returns receipt_review.html partial with editable table.
    """
    all_items = []
    all_warnings = []
    all_contradictions = []
    last_upload_id = None
    failed_files = []

    llm_cfg = await get_active_llm_config(db)
    svc = PreferenceService(db)

    for pdf_file in receipt_pdfs:
        pdf_bytes = await pdf_file.read()
        raw_text, extract_warnings = extract_receipt_text(pdf_bytes)
        filename = pdf_file.filename or "receipt.pdf"

        if len(raw_text.strip()) < 50:
            failed_files.append(filename)
            all_warnings.append(f"{filename}: could not extract text")
            continue

        try:
            parsed = await parse_receipt_with_llm(
                raw_text,
                llm_cfg["api_key"],
                llm_cfg["provider"],
                llm_cfg["model"],
            )
        except RuntimeError as e:
            failed_files.append(filename)
            all_warnings.append(f"{filename}: {str(e)}")
            continue

        _clean_items, contradictions = await svc.detect_contradictions(parsed.items)

        # Persist the upload audit record
        file_warnings = parsed.parse_warnings + extract_warnings
        upload = ReceiptUpload(
            filename=filename,
            items_extracted=len(parsed.items),
            parse_status="parsed",
            parse_warnings=json.dumps(file_warnings),
        )
        db.add(upload)
        await db.commit()
        await db.refresh(upload)

        all_items.extend(parsed.items)
        all_warnings.extend(file_warnings)
        all_contradictions.extend(contradictions)
        last_upload_id = upload.id

    # If every file failed
    if not all_items:
        error_detail = "; ".join(all_warnings) if all_warnings else "Unknown error"
        return templates.TemplateResponse(
            request,
            "partials/receipt_review.html",
            {
                "error": True,
                "error_heading": "Could not read receipts",
                "error_body": (
                    f"Failed to parse {len(failed_files)} file(s). "
                    f"{error_detail}. "
                    "Try different receipts or add preferences manually."
                ),
            },
        )

    # Store parsed state in DB (session cookies have 4KB limit, receipts exceed that)
    if last_upload_id:
        from sqlalchemy import select as sa_select
        from app.models.receipt_upload import ReceiptUpload as RU
        result = await db.execute(sa_select(RU).where(RU.id == last_upload_id))
        upload_record = result.scalar_one_or_none()
        if upload_record:
            upload_record.parsed_items_json = json.dumps([item.model_dump() for item in all_items])
            upload_record.contradictions_json = json.dumps([c.model_dump() for c in all_contradictions])
            await db.commit()

    # Store only the upload_id in session (small enough for cookie)
    request.session["receipt_upload_id"] = last_upload_id

    if failed_files:
        all_warnings.insert(0, f"{len(failed_files)} file(s) could not be parsed: {', '.join(failed_files)}")

    return templates.TemplateResponse(
        request,
        "partials/receipt_review.html",
        {
            "error": False,
            "items": all_items,
            "contradictions": all_contradictions,
            "warnings": all_warnings,
            "upload_id": last_upload_id,
        },
    )


@router.post("/receipt/resolve", response_class=HTMLResponse)
async def receipt_resolve_contradiction(
    request: Request,
    contradiction_index: int = Form(...),
    resolution: str = Form(...),
):
    """Resolve a single contradiction ('new_preference' or 'one_time').

    Updates contradictions in DB and returns refreshed contradictions partial.
    """
    upload_id: Optional[int] = request.session.get("receipt_upload_id")
    contradictions_raw: list[dict] = []

    if upload_id:
        from sqlalchemy import select as sa_select
        from app.models.receipt_upload import ReceiptUpload as RU
        from app.database import get_session as _gs
        async for db in _gs():
            result = await db.execute(sa_select(RU).where(RU.id == upload_id))
            upload_record = result.scalar_one_or_none()
            if upload_record and upload_record.contradictions_json:
                contradictions_raw = json.loads(upload_record.contradictions_json)

            if 0 <= contradiction_index < len(contradictions_raw):
                contradictions_raw[contradiction_index]["resolution"] = resolution
                if upload_record:
                    upload_record.contradictions_json = json.dumps(contradictions_raw)
                    await db.commit()

    # Re-build ContradictionCandidate objects for template
    contradictions = [ContradictionCandidate(**c) for c in contradictions_raw]
    unresolved = [c for c in contradictions if c.resolution is None]

    if not unresolved:
        return HTMLResponse("")  # All resolved — remove the panel

    return templates.TemplateResponse(
        request,
        "partials/receipt_contradictions.html",
        {"contradictions": unresolved},
    )


@router.post("/receipt/save", response_class=HTMLResponse)
async def receipt_save(
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    """Save confirmed receipt items to the preference store.

    Loads items and contradiction resolutions from session.
    Clears session keys on completion.
    Returns refreshed preference list with success message.
    """
    upload_id: Optional[int] = request.session.get("receipt_upload_id")

    # Read parsed items from DB (not session — cookie has 4KB limit)
    items_raw: list[dict] = []
    contradictions_raw: list[dict] = []
    if upload_id:
        from sqlalchemy import select as sa_select
        from app.models.receipt_upload import ReceiptUpload as RU
        result = await db.execute(sa_select(RU).where(RU.id == upload_id))
        upload_record = result.scalar_one_or_none()
        if upload_record and upload_record.parsed_items_json:
            items_raw = json.loads(upload_record.parsed_items_json)
        if upload_record and upload_record.contradictions_json:
            contradictions_raw = json.loads(upload_record.contradictions_json)

    # Build a mapping of item_index → is_one_time from resolved contradictions
    one_time_indices: set[int] = set()
    for c in contradictions_raw:
        if c.get("resolution") == "one_time":
            one_time_indices.add(c["new_item_index"])

    svc = PreferenceService(db)
    confirmed_count = 0

    for idx, item_dict in enumerate(items_raw):
        try:
            item = ReceiptLineItem(**item_dict)
            is_one_time = idx in one_time_indices
            await svc.upsert_from_receipt_item(item, is_one_time=is_one_time)
            confirmed_count += 1
        except Exception:
            continue  # Skip malformed items; don't abort the whole save

    # Update audit record
    if upload_id:
        from sqlalchemy import select
        from app.models.receipt_upload import ReceiptUpload as RU
        result = await db.execute(select(RU).where(RU.id == upload_id))
        upload = result.scalar_one_or_none()
        if upload:
            upload.parse_status = "confirmed"
            upload.items_confirmed = confirmed_count
            db.add(upload)

    await db.commit()

    # Clear session keys
    for key in ("receipt_items", "receipt_contradictions", "receipt_upload_id"):
        request.session.pop(key, None)

    # Return the updated preference list with a success banner
    entries = await svc.list_preferences()
    return templates.TemplateResponse(
        request,
        "partials/pref_list.html",
        {
            "preferences": entries,
            "query": None,
            "save_success": True,
            "saved_count": confirmed_count,
        },
    )


# ---------------------------------------------------------------------------
# NL preference chat endpoints
# ---------------------------------------------------------------------------


async def parse_preference_nl(
    conversation_history: list[dict],
    api_key: str,
    provider: str,
    model: str,
) -> PreferenceDelta:
    """Parse a natural language preference update into a structured delta."""
    model_str = f"{provider}/{model}" if "/" not in model else model
    client = instructor.from_provider(f"litellm/{model_str}", async_client=True)

    system_prompt = (
        "You are a preference update assistant for a grocery shopping app. "
        "The user wants to update their brand/product preferences. "
        "Interpret their message and return a structured action. "
        "If the intent is unclear, set action='clarify' and ask a specific question. "
        "For clear intents: use 'replace' to switch brands, 'add' to add a new preference, "
        "'remove' to delete a preference. Always include a human_summary describing the change."
    )

    messages = [{"role": "system", "content": system_prompt}] + conversation_history

    return await client.create(
        model=model_str,
        messages=messages,
        response_model=PreferenceDelta,
        max_tokens=500,
        max_retries=2,
        api_key=api_key,
    )


@router.post("/chat", response_class=HTMLResponse)
async def preference_chat(
    request: Request,
    message: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    """HTMX partial: process a natural language preference update message.

    Appends user + assistant bubbles to #chat-history via hx-swap="beforeend".
    When the LLM returns a concrete action (not 'clarify'), stores the delta in
    session and returns a confirmation preview bubble with Apply/Discard buttons.
    """
    history: list[dict] = request.session.get("pref_chat_history", [])
    history.append({"role": "user", "content": message})

    # Cap LLM context at last 10 messages to control token cost (Pitfall 5)
    llm_history = history[-10:]

    llm_cfg = await get_active_llm_config(db)

    try:
        delta = await parse_preference_nl(
            llm_history,
            llm_cfg["api_key"],
            llm_cfg["provider"],
            llm_cfg["model"],
        )
    except Exception as e:
        # LLM failure — show inline error bubble
        history.append({"role": "assistant", "content": "error"})
        request.session["pref_chat_history"] = history
        return templates.TemplateResponse(
            request,
            "partials/chat_message.html",
            {
                "user_message": message,
                "role": "assistant",
                "message": "Something went wrong. Try again or edit your preferences directly in the list.",
                "needs_confirm": False,
                "is_error": True,
            },
        )

    history.append({"role": "assistant", "content": delta.human_summary})
    request.session["pref_chat_history"] = history

    if delta.action == "clarify":
        return templates.TemplateResponse(
            request,
            "partials/chat_message.html",
            {
                "user_message": message,
                "role": "assistant",
                "message": delta.clarification_question or delta.human_summary,
                "needs_confirm": False,
                "is_error": False,
            },
        )

    # Non-clarify action: store delta and return confirmation preview
    request.session["pending_delta"] = delta.model_dump()
    return templates.TemplateResponse(
        request,
        "partials/chat_message.html",
        {
            "user_message": message,
            "role": "assistant",
            "message": delta.human_summary,
            "needs_confirm": True,
            "is_error": False,
            "delta": delta.model_dump(),
        },
    )


@router.post("/chat/apply", response_class=HTMLResponse)
async def preference_chat_apply(
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    """HTMX partial: apply a confirmed NL preference delta.

    Loads pending_delta from session, calls apply_nl_delta, clears session key.
    Returns a system confirmation bubble appended to #chat-history.
    """
    pending_raw: Optional[dict] = request.session.get("pending_delta")

    if not pending_raw:
        return templates.TemplateResponse(
            request,
            "partials/chat_message.html",
            {
                "user_message": None,
                "role": "assistant",
                "message": "No pending change to apply.",
                "needs_confirm": False,
                "is_error": True,
            },
        )

    delta = PreferenceDelta(**pending_raw)
    await PreferenceService(db).apply_nl_delta(delta)
    await db.commit()

    # Clear pending delta from session
    request.session.pop("pending_delta", None)

    return templates.TemplateResponse(
        request,
        "partials/chat_message.html",
        {
            "user_message": None,
            "role": "system",
            "message": "Done! Your preferences have been updated.",
            "needs_confirm": False,
            "is_error": False,
        },
    )
