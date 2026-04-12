"""Receipt PDF parsing pipeline: pdfplumber text extraction + LLM normalization via Instructor."""
from io import BytesIO

import instructor
import pdfplumber

from app.schemas.preferences import ParsedReceipt


def extract_receipt_text(pdf_bytes: bytes) -> tuple[str, list[str]]:
    """Extract text from a PDF receipt using pdfplumber.

    Uses layout=True extraction for each page; falls back to extract_words()
    if layout extraction yields no content.

    Returns (combined_text, warnings) where warnings is a list of issue strings.
    On any extraction error, returns ("", [error_message]).
    """
    try:
        warnings: list[str] = []
        pages_text: list[str] = []

        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text(layout=True)
                if not text or not text.strip():
                    # Fallback: join words with spaces
                    words = page.extract_words()
                    text = " ".join(w["text"] for w in words) if words else ""
                if text:
                    pages_text.append(text)

        combined = "\n".join(pages_text)

        if len(combined.strip()) < 50:
            warnings.append(
                "Very little text extracted -- PDF may be image-based or encrypted"
            )

        return combined, warnings

    except Exception as e:
        return "", [f"PDF extraction failed: {str(e)}"]


async def parse_receipt_with_llm(
    raw_text: str,
    api_key: str,
    provider: str,
    model: str,
) -> ParsedReceipt:
    """Normalize raw receipt text into structured ReceiptLineItem objects using an LLM.

    Follows the same Instructor/LiteLLM pattern as llm_service.parse_shopping_list.
    The system prompt handles Fry's-specific abbreviations (PRIV SEL, ORG, etc.).

    Raises RuntimeError on LLM or parsing failure.
    """
    try:
        model_str = f"{provider}/{model}" if "/" not in model else model
        client = instructor.from_provider(
            f"litellm/{model_str}",
            async_client=True,
        )

        system_prompt = (
            "You are a grocery receipt parser for Fry's/Kroger receipts. "
            "Fry's uses heavy abbreviations: PRIV SEL = Private Selection, ORG = Organic, "
            "CHCKN = Chicken, BRST = Breast, BN FREE = Bone Free. "
            "For each line item: expand abbreviations, infer brand from product name, "
            "assign a semantic product_category (e.g. 'milk', 'cheddar cheese'). "
            "Set confidence < 0.7 if you are guessing the brand or category. "
            "Skip non-food items (tax lines, totals, loyalty savings). "
            "Return parse_warnings for any lines you could not interpret."
        )

        result = await client.create(
            model=model_str,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Parse this receipt:\n\n{raw_text}"},
            ],
            response_model=ParsedReceipt,
            max_tokens=2000,
            max_retries=2,
            api_key=api_key,
        )
        return result

    except Exception as e:
        raise RuntimeError(f"Receipt parsing failed: {str(e)}") from e
