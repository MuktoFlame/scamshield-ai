"""Shared test configuration.

Tests must be hermetic: no network, no LLM quota usage. A developer's local
.env (with a real GEMINI_API_KEY) must not change test behavior, so the key
is cleared for every test — all LLM-dependent code paths are exercised via
their deterministic fallbacks, and LLM behavior itself is covered by mocks.
"""
import pytest

from app.config import settings


@pytest.fixture(autouse=True)
def _no_llm_in_tests(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "")
