from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import current_user
from ..db import get_db
from ..models import LinkRedeemRequest

router = APIRouter(prefix="/api/caregiver", tags=["caregiver"])

CODE_TTL_MINUTES = 15


@router.post("/code")
def create_link_code(user: Annotated[dict, Depends(current_user)]):
    """A senior generates a short-lived 6-digit code for a caregiver to redeem."""
    if user["role"] != "senior":
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Only senior accounts can generate link codes")
    db = get_db()
    code = f"{secrets.randbelow(1_000_000):06d}"
    db.link_codes.delete_many({"senior_id": user["_id"]})
    db.link_codes.insert_one({
        "_id": secrets.token_hex(8),
        "code": code,
        "senior_id": user["_id"],
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=CODE_TTL_MINUTES),
    })
    return {"code": code, "expires_in_minutes": CODE_TTL_MINUTES}


@router.post("/link")
def redeem_link_code(body: LinkRedeemRequest,
                     user: Annotated[dict, Depends(current_user)]):
    """A caregiver redeems a senior's code to gain read-only history access."""
    if user["role"] != "caregiver":
        raise HTTPException(status.HTTP_403_FORBIDDEN,
                            "Only caregiver accounts can redeem link codes")
    db = get_db()
    entry = db.link_codes.find_one({"code": body.code})
    if entry is None or entry["expires_at"].replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_404_NOT_FOUND,
                            "Code not found or expired — ask for a new one")
    if entry["senior_id"] == user["_id"]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "You cannot link to yourself")
    db.links.update_one(
        {"caregiver_id": user["_id"], "senior_id": entry["senior_id"]},
        {"$set": {"linked_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    db.link_codes.delete_one({"_id": entry["_id"]})
    senior = db.users.find_one({"_id": entry["senior_id"]})
    return {"linked": True,
            "senior": {"id": entry["senior_id"], "name": senior["name"]}}


@router.get("/links")
def my_links(user: Annotated[dict, Depends(current_user)]):
    """List accounts linked to me (as caregiver) or watching me (as senior)."""
    db = get_db()
    if user["role"] == "caregiver":
        links = list(db.links.find({"caregiver_id": user["_id"]}))
        ids = [l["senior_id"] for l in links]
        people = {u["_id"]: u for u in db.users.find({"_id": {"$in": ids}})}
        return {"links": [
            {"id": i, "name": people[i]["name"], "role": "senior"}
            for i in ids if i in people
        ]}
    links = list(db.links.find({"senior_id": user["_id"]}))
    ids = [l["caregiver_id"] for l in links]
    people = {u["_id"]: u for u in db.users.find({"_id": {"$in": ids}})}
    return {"links": [
        {"id": i, "name": people[i]["name"], "role": "caregiver"}
        for i in ids if i in people
    ]}


@router.delete("/link/{other_id}")
def unlink(other_id: str, user: Annotated[dict, Depends(current_user)]):
    """Either side of a link can remove it."""
    db = get_db()
    result = db.links.delete_many({"$or": [
        {"caregiver_id": user["_id"], "senior_id": other_id},
        {"caregiver_id": other_id, "senior_id": user["_id"]},
    ]})
    if result.deleted_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such link")
    return {"unlinked": True}
