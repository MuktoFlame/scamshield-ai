"""ScamShield AI — MCP server.

Exposes the same detection services the web app uses as Model Context
Protocol tools. MCP is an open standard, so any MCP-compatible client — AI
assistants, agent frameworks, IDE agents, workflow tools, or custom code —
can call ScamShield as part of its own reasoning:

    check_message      - scam-risk analysis of an SMS/email/transcript
    check_url          - phishing analysis of a web address
    check_news         - credibility + fact-check of an article or claim
    fact_check_claim   - RAG verdict for a single factual claim
    check_product      - fraud assessment of a marketplace listing

Run:  python mcp_server/server.py            (stdio transport)
See the README for client configuration, or demo_client.py for a
standalone demonstration that needs no AI application.
"""
from __future__ import annotations

import sys
from pathlib import Path

# The backend package lives next to this folder; make it importable when the
# server is launched from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastmcp import FastMCP

from app.services import (explainer, factcheck, guidance, news_checker,
                          pipeline, product_checker, safe_fetch, url_checker)

mcp = FastMCP(
    "scamshield",
    instructions="Scam, phishing, misinformation and fraud detection tools "
                 "backed by trained ML models, a rule engine, and RAG "
                 "fact-checking.",
)


@mcp.tool
def check_message(text: str, language: str = "en") -> dict:
    """Analyze a suspicious message (SMS, email, chat, call transcript) for
    scam risk. Returns risk level, score, evidence-backed red flags, and a
    plain-language recommendation."""
    report = pipeline.analyze(text)
    tips = guidance.retrieve(text[:200])
    report = explainer.explain(text, report, language, guidance=tips)
    result = report.to_dict()
    result["guidance"] = tips
    return result


@mcp.tool
def check_url(url: str, language: str = "en") -> dict:
    """Analyze a web address for phishing risk: lexical analysis, a trained
    phishing-URL model, and safe live page inspection."""
    try:
        return url_checker.check(url, language)
    except safe_fetch.UnsafeUrl as exc:
        return {"error": str(exc)}


@mcp.tool
def check_news(text: str, language: str = "en") -> dict:
    """Credibility-check an article or headline: writing-style analysis by a
    trained model plus RAG fact-checking of its main claims against
    Wikipedia."""
    return news_checker.check(text, language)


@mcp.tool
def fact_check_claim(claim: str) -> dict:
    """Fact-check one factual claim: retrieves Wikipedia evidence (BM25) and
    returns supported / refuted / unverifiable with sources."""
    evidence = factcheck.retrieve_evidence(claim)
    verdict = factcheck.judge(claim, evidence)
    return {
        "claim": claim,
        "verdict": verdict["verdict"],
        "rationale": verdict["rationale"],
        "sources": [{"title": e["source"], "url": e["url"]} for e in evidence[:3]],
    }


@mcp.tool
def check_product(title: str, description: str = "", price: str = "",
                  platform: str = "", seller_info: str = "") -> dict:
    """Assess an online product listing for fraud/counterfeit risk from its
    title, price, description, platform and seller details."""
    return product_checker.check(title=title, description=description,
                                 price=price, platform=platform,
                                 seller_info=seller_info)


if __name__ == "__main__":
    mcp.run()
