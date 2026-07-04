from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import current_user
from ..db import get_db

router = APIRouter(prefix="/api", tags=["history"])


def _serialize(scan: dict) -> dict:
    return {
        "id": scan["_id"],
        "type": scan.get("type", "message"),
        "channel": scan.get("channel", "other"),
        "text": scan["text"],
        "result": scan["result"],
        "created_at": scan["created_at"].isoformat(),
    }


@router.get("/history")
def my_history(user: Annotated[dict, Depends(current_user)], limit: int = 50):
    scans = (get_db().scans.find({"user_id": user["_id"]})
             .sort("created_at", -1).limit(min(limit, 200)))
    return {"scans": [_serialize(s) for s in scans]}


@router.get("/history/{senior_id}")
def linked_history(senior_id: str,
                   user: Annotated[dict, Depends(current_user)],
                   limit: int = 50):
    """Caregiver read-only view of a linked senior's scans."""
    db = get_db()
    link = db.links.find_one({"caregiver_id": user["_id"],
                              "senior_id": senior_id})
    if link is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "You are not linked to this account")
    scans = (db.scans.find({"user_id": senior_id})
             .sort("created_at", -1).limit(min(limit, 200)))
    senior = db.users.find_one({"_id": senior_id})
    return {
        "senior": {"id": senior_id, "name": senior["name"] if senior else "?"},
        "scans": [_serialize(s) for s in scans],
    }
