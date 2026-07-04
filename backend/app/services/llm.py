"""Unified Gemini client wrapper.

Every LLM call in the app goes through here so that availability checks,
error handling, and model selection live in one place.

Model selection: free-tier quotas differ per model, so calls walk the chain
configured in settings (GEMINI_MODEL + GEMINI_FALLBACK_MODELS). A model that
answers is remembered and tried first next time; on quota exhaustion or
model-not-found errors the next model in the chain is tried.

All callers must handle a None return (no API key, all quotas exhausted,
network failure) with their own deterministic fallback — an LLM outage must
never break a check.
"""
from __future__ import annotations

import json
import logging

from ..config import settings

log = logging.getLogger(__name__)

_preferred_model: str | None = None  # first model that worked this process


def available() -> bool:
    return bool(settings.gemini_api_key)


def _client():
    from google import genai
    return genai.Client(api_key=settings.gemini_api_key)


def _model_chain() -> list[str]:
    chain = settings.gemini_model_chain
    if _preferred_model and _preferred_model in chain:
        chain = ([_preferred_model]
                 + [m for m in chain if m != _preferred_model])
    return chain


def _generate(contents, config) -> str | None:
    """Run generate_content across the model chain. Returns response text."""
    global _preferred_model
    if not available():
        return None
    client = _client()
    for model in _model_chain():
        try:
            resp = client.models.generate_content(
                model=model, contents=contents, config=config)
            _preferred_model = model
            return resp.text or ""
        except Exception as exc:
            log.warning("Gemini model %s failed (%s); trying next",
                        model, type(exc).__name__)
    log.warning("All Gemini models in the chain failed")
    return None


def generate_json(prompt: str, schema: dict, system: str | None = None,
                  temperature: float = 0.3,
                  max_output_tokens: int = 800) -> dict | None:
    """Structured-output call. Returns parsed dict, or None on any failure."""
    try:
        from google.genai import types
    except ImportError:
        return None
    config = types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json",
        response_schema=schema,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
    text = _generate(prompt, config)
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        log.warning("Gemini returned non-JSON despite schema")
        return None


def generate_vision(image_bytes: bytes, mime_type: str, prompt: str,
                    temperature: float = 0.0,
                    max_output_tokens: int = 2000) -> str | None:
    """Image + prompt -> text. Returns None on any failure (callers fall back)."""
    try:
        from google.genai import types
    except ImportError:
        return None
    contents = [types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt]
    config = types.GenerateContentConfig(
        temperature=temperature, max_output_tokens=max_output_tokens)
    text = _generate(contents, config)
    return text.strip() if text is not None else None
