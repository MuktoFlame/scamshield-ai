from __future__ import annotations

import base64
import binascii
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..auth import optional_user
from ..db import get_db
from ..models import ImageScanRequest, ScanRequest
from ..services import explainer, guidance, ocr, pipeline
from ..limiter import limiter

router = APIRouter(prefix="/api", tags=["scan"])

MAX_IMAGE_BYTES = 6 * 1024 * 1024


def save_check(check_type: str, text: str, result: dict, user: dict | None,
               channel: str = "other", **extra) -> dict:
    """Persist any checker's result as typed history (when signed in)."""
    record_id = uuid.uuid4().hex
    if user is not None:
        get_db().scans.insert_one({
            "_id": record_id,
            "user_id": user["_id"],
            "type": check_type,
            "channel": channel,
            "text": text,
            "result": result,
            "created_at": datetime.now(timezone.utc),
            **extra,
        })
    return {"id": record_id, "saved": user is not None, **result}


def _run_scan(text: str, channel: str, language: str,
              user: dict | None, extracted_from_image: bool = False) -> dict:
    report = pipeline.analyze(text)
    flag_terms = " ".join(f["title"] for f in report.flags)
    tips = guidance.retrieve(f"{flag_terms} {text[:200]}")
    report = explainer.explain(text, report, language, guidance=tips)
    result = report.to_dict()
    result["guidance"] = tips
    return save_check("message", text, result, user,
                      channel=channel, from_image=extracted_from_image)


@router.post("/scan")
@limiter.limit("20/minute")
def scan(request: Request, body: ScanRequest,
         user: Annotated[dict | None, Depends(optional_user)]):
    """Analyze a message. Works for guests; saves history for logged-in users."""
    return _run_scan(body.text, body.channel, body.language, user)


@router.post("/scan/image")
@limiter.limit("10/minute")
def scan_image(request: Request, body: ImageScanRequest,
               user: Annotated[dict | None, Depends(optional_user)]):
    """Extract the message text from a screenshot, then analyze it."""
    try:
        image_bytes = base64.b64decode(body.image_b64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid image data")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            "Image too large (max 6 MB)")

    try:
        text = ocr.extract_text(image_bytes, body.mime_type)
    except ocr.OcrUnavailable as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    except Exception:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY,
                            "Could not read the screenshot. Please try again "
                            "or paste the message text instead.")
    if text is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "No readable message found in that image. Please "
                            "try a clearer screenshot or paste the text.")

    response = _run_scan(text, body.channel, body.language, user,
                         extracted_from_image=True)
    response["extracted_text"] = text
    return response
