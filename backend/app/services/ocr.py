"""Screenshot text extraction via Gemini vision.

Lets a user scan a screenshot of a suspicious message (common for elderly
users who receive scams on a phone and can't easily copy the text). The
extracted text then flows through the exact same grounded pipeline as pasted
text — the vision model only transcribes, it never judges.
"""
from __future__ import annotations

import logging

from . import llm

log = logging.getLogger(__name__)

_PROMPT = (
    "Extract the complete text of the message shown in this screenshot. "
    "Include the sender name/number if visible. Return ONLY the transcribed "
    "text with no commentary. If the image contains no readable message, "
    "return exactly: [NO_TEXT_FOUND]"
)


class OcrUnavailable(Exception):
    """Raised when no vision model is configured."""


def extract_text(image_bytes: bytes, mime_type: str) -> str | None:
    """Transcribe a screenshot. Returns None when no text is found."""
    if not llm.available():
        raise OcrUnavailable(
            "Screenshot reading requires the AI service, which is not "
            "configured on this server. Please paste the message text instead."
        )
    text = llm.generate_vision(image_bytes, mime_type, _PROMPT)
    if text is None:
        raise RuntimeError("vision call failed")
    if not text or "[NO_TEXT_FOUND]" in text:
        return None
    return text
