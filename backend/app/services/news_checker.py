"""News & Fact Check: style classifier + RAG claim verification, fused.

The style model judges *how* the text is written; the fact-check pipeline
judges *what it claims* against retrieved Wikipedia evidence. The fusion is
deterministic: any refuted claim floors the risk at "high-ish" regardless of
how sober the writing style is.
"""
from __future__ import annotations

import logging

from . import classifier, explainer, factcheck
from .pipeline import RiskReport, level_for
from .rules import Flag

log = logging.getLogger(__name__)


def _claim_flags(claims: list[dict]) -> list[Flag]:
    flags: list[Flag] = []
    refuted = [c for c in claims if c["verdict"] == "refuted"]
    unverifiable = [c for c in claims if c["verdict"] == "unverifiable"]
    if refuted:
        flags.append(Flag(
            "refuted_claims", "Contains claims contradicted by references",
            "One or more factual claims in this text are contradicted by "
            "reference material.",
            0.8, [c["claim"][:100] for c in refuted[:3]]))
    if len(unverifiable) == len(claims) and claims:
        flags.append(Flag(
            "unverified_claims", "Key claims could not be verified",
            "The main claims could not be confirmed against reference "
            "material. Treat them with caution until confirmed elsewhere.",
            0.3, [c["claim"][:100] for c in unverifiable[:3]]))
    return flags


def check(text: str, language: str = "en", source_title: str = "",
          guidance: list[dict] | None = None) -> dict:
    style_prob = classifier.news_probability(text)
    claims = factcheck.check_claims(text)

    flags = _claim_flags(claims)
    if style_prob is not None and style_prob >= 0.6:
        flags.insert(0, Flag(
            "sensational_style", "Written like typical misinformation",
            "The writing style — tone, phrasing, structure — closely matches "
            "articles from known misinformation sources. Style alone does not "
            "make something false, which is why the claims are also checked.",
            0.5, [f"style match {style_prob:.0%}"]))

    n = len(claims) or 1
    refuted = sum(c["verdict"] == "refuted" for c in claims)
    supported = sum(c["verdict"] == "supported" for c in claims)
    unverifiable = n - refuted - supported
    claim_score = (refuted * 1.0 + unverifiable * 0.5) / n

    style = style_prob if style_prob is not None else 0.5
    score = 0.55 * style + 0.45 * claim_score
    if refuted:
        score = max(score, 0.7)          # a contradicted claim dominates
    elif supported and not unverifiable:
        score = min(score, 0.45)         # fully verified content can't be "high"
    score = round(min(score, 1.0), 4)

    report = RiskReport(
        risk_level=level_for(score),
        risk_score=score,
        confidence=round(1.0 - (unverifiable / n) * 0.5, 4),
        classifier_probability=style_prob,
        rule_score=round(claim_score, 4),
        flags=[f.to_dict() for f in flags],
    )
    subject = "news article or claim"
    header = f"TITLE: {source_title}\n" if source_title else ""
    report = explainer.explain(header + text[:3000], report, language,
                               subject=subject, guidance=guidance)

    result = report.to_dict()
    result.update({
        "style_score": style_prob,
        "claims": claims,
        "checked_claims": n if claims else 0,
    })
    return result
