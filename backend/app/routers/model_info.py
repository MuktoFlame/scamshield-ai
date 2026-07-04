"""Transparency endpoint: serves the classifier's training metrics."""
from __future__ import annotations

from fastapi import APIRouter

from ..services.classifier import model_info

router = APIRouter(prefix="/api", tags=["model"])


@router.get("/model/info")
def get_model_info():
    return model_info()
