from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from ..auth import create_token, hash_password, verify_password
from ..db import get_db
from ..models import AuthResponse, LoginRequest, RegisterRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _public(user: dict) -> dict:
    return {"id": user["_id"], "name": user["name"],
            "email": user["email"], "role": user["role"]}


@router.post("/register", response_model=AuthResponse,
             status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    db = get_db()
    if db.users.find_one({"email": body.email.lower()}):
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "An account with this email already exists")
    user = {
        "_id": uuid.uuid4().hex,
        "name": body.name.strip(),
        "email": body.email.lower(),
        "password_hash": hash_password(body.password),
        "role": body.role,
        "created_at": datetime.now(timezone.utc),
    }
    db.users.insert_one(user)
    return AuthResponse(token=create_token(user["_id"], user["role"]),
                        user=_public(user))


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest):
    user = get_db().users.find_one({"email": body.email.lower()})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "Incorrect email or password")
    return AuthResponse(token=create_token(user["_id"], user["role"]),
                        user=_public(user))
