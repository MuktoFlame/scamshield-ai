"""ScamShield AI — FastAPI application entry point."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .config import settings
from .limiter import limiter
from .routers import (auth, caregiver, checks, history, model_info, patterns,
                      scan)

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="ScamShield AI",
    description=(
        "Plain-language scam & phishing risk assessment. Hybrid pipeline: "
        "rule engine + TF-IDF/LogisticRegression classifier + LLM explanation."
    ),
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(scan.router)
app.include_router(checks.router)
app.include_router(history.router)
app.include_router(caregiver.router)
app.include_router(patterns.router)
app.include_router(model_info.router)


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok", "service": "scamshield-api"}
