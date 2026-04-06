"""Unit tests for receipt_parser.py: pdfplumber extraction and LLM normalization.

All pdfplumber and LLM calls are mocked — these tests verify parser logic only.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


# ---------------------------------------------------------------------------
# test_extract_receipt_text_valid_pdf
# ---------------------------------------------------------------------------

def test_extract_receipt_text_valid_pdf():
    """Given a page with extractable text, returns text and empty warnings."""
    from app.services.receipt_parser import extract_receipt_text

    mock_page = MagicMock()
    mock_page.extract_text.return_value = (
        "FRYS FOOD STORE #123\n"
        "TILLAMOOK CHEDDAR  $8.49\n"
        "ORG VALLEY 2% MILK  $4.99\n"
        "TAX  $0.52\n"
        "TOTAL  $14.00"
    )
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    with patch("app.services.receipt_parser.pdfplumber") as mock_pdfplumber:
        mock_pdfplumber.open.return_value = mock_pdf
        text, warnings = extract_receipt_text(b"fake pdf bytes")

    assert len(text) > 50
    assert "TILLAMOOK" in text
    assert len(warnings) == 0


# ---------------------------------------------------------------------------
# test_extract_receipt_text_empty_pdf
# ---------------------------------------------------------------------------

def test_extract_receipt_text_empty_pdf():
    """Given a PDF page with no extractable text, returns warning about image-based PDF."""
    from app.services.receipt_parser import extract_receipt_text

    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""
    mock_page.extract_words.return_value = []  # words fallback also empty
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)

    with patch("app.services.receipt_parser.pdfplumber") as mock_pdfplumber:
        mock_pdfplumber.open.return_value = mock_pdf
        text, warnings = extract_receipt_text(b"image pdf bytes")

    assert len(warnings) == 1
    assert "image" in warnings[0].lower() or "little" in warnings[0].lower()


# ---------------------------------------------------------------------------
# test_extract_receipt_text_invalid_bytes
# ---------------------------------------------------------------------------

def test_extract_receipt_text_invalid_bytes():
    """Given non-PDF bytes, returns empty string and an error warning."""
    from app.services.receipt_parser import extract_receipt_text

    with patch("app.services.receipt_parser.pdfplumber") as mock_pdfplumber:
        mock_pdfplumber.open.side_effect = Exception("not a PDF")
        text, warnings = extract_receipt_text(b"not a real pdf")

    assert text == ""
    assert len(warnings) == 1
    assert "failed" in warnings[0].lower() or "error" in warnings[0].lower() or "extraction" in warnings[0].lower()


# ---------------------------------------------------------------------------
# test_parse_receipt_with_llm
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_parse_receipt_with_llm():
    """Given raw receipt text, Instructor client returns a ParsedReceipt with expected items."""
    from app.services.receipt_parser import parse_receipt_with_llm
    from app.schemas.preferences import ParsedReceipt, ReceiptLineItem

    mock_result = ParsedReceipt(
        items=[
            ReceiptLineItem(
                product_name="Medium Cheddar",
                brand="Tillamook",
                product_category="cheddar cheese",
                confidence=0.95,
                price=8.49,
            ),
            ReceiptLineItem(
                product_name="2% Milk",
                brand="Organic Valley",
                product_category="milk",
                confidence=0.90,
                price=4.99,
            ),
        ],
        parse_warnings=[],
    )

    mock_client = AsyncMock()
    mock_client.create = AsyncMock(return_value=mock_result)

    with patch("app.services.receipt_parser.instructor") as mock_instructor:
        mock_instructor.from_provider.return_value = mock_client
        result = await parse_receipt_with_llm(
            "FRYS FOOD STORE #123\nTILLAMOOK CHEDDAR $8.49\nORG VALLEY 2% MILK $4.99",
            api_key="fake-key",
            provider="anthropic",
            model="claude-3-haiku-20240307",
        )

    assert len(result.items) == 2
    assert result.items[0].brand == "Tillamook"
    assert result.items[1].product_category == "milk"
    assert len(result.parse_warnings) == 0
