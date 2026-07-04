"""Database access. MongoDB Atlas in production; mongomock when no MONGO_URI
is configured so the whole stack runs locally with zero external services.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from .config import settings

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_db():
    if settings.mongo_uri:
        from pymongo import MongoClient
        client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
        log.info("Connected to MongoDB Atlas")
    else:
        import mongomock
        client = mongomock.MongoClient()
        log.warning("MONGO_URI not set — using in-memory mongomock "
                    "(data will not persist across restarts)")
    db = client[settings.mongo_db_name]
    _ensure_indexes(db)
    return db


def _ensure_indexes(db) -> None:
    db.users.create_index("email", unique=True)
    db.scans.create_index([("user_id", 1), ("created_at", -1)])
    db.link_codes.create_index("code", unique=True)
    db.link_codes.create_index("expires_at", expireAfterSeconds=0)
    db.links.create_index([("caregiver_id", 1), ("senior_id", 1)], unique=True)
