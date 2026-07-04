"""Risk fusion: combine the rule engine and the ML classifier into one score,
then hand the grounded result to the explainer for plain-language output.

Fusion strategy: the final score is a weighted blend, but either signal can
raise the floor on its own — a message the classifier is 99% sure about should
not be diluted by an absence of keyword flags, and vice versa. Deterministic
and unit-tested; the LLM never decides the risk level, only explains it.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import classifier, rules

CLASSIFIER_WEIGHT = 0.55
RULES_WEIGHT = 0.45
HIGH_THRESHOLD = 0.65
MEDIUM_THRESHOLD = 0.30


@dataclass
class RiskReport:
    risk_level: str                 # "low" | "medium" | "high"
    risk_score: float               # fused 0..1
    confidence: float               # agreement between the two signals, 0..1
    classifier_probability: float | None
    rule_score: float
    flags: list[dict] = field(default_factory=list)
    summary: str = ""
    recommended_action: str = ""
    explanation_source: str = ""    # "llm" | "rules"

    def to_dict(self) -> dict:
        return {
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "classifier_probability": self.classifier_probability,
            "rule_score": self.rule_score,
            "flags": self.flags,
            "summary": self.summary,
            "recommended_action": self.recommended_action,
            "explanation_source": self.explanation_source,
        }


def fuse(clf_prob: float | None, rule_score: float) -> tuple[float, float]:
    """Blend the two signals. Returns (risk_score, confidence)."""
    if clf_prob is None:
        return round(rule_score, 4), 0.5

    blended = CLASSIFIER_WEIGHT * clf_prob + RULES_WEIGHT * rule_score
    # Either strong signal alone should carry: take max with slightly
    # discounted individual signals so one confident detector wins.
    score = max(blended, clf_prob * 0.9, rule_score * 0.9)

    # Confidence = how much the two signals agree (1 - normalized disagreement),
    # scaled up when both are decisive (far from 0.5).
    agreement = 1.0 - abs(clf_prob - rule_score)
    decisiveness = (abs(clf_prob - 0.5) + abs(rule_score - 0.5))
    confidence = min(1.0, 0.5 * agreement + 0.5 * decisiveness)
    return round(min(score, 1.0), 4), round(confidence, 4)


def level_for(score: float) -> str:
    if score >= HIGH_THRESHOLD:
        return "high"
    if score >= MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def analyze(text: str) -> RiskReport:
    """Run the full grounded pipeline (rules + classifier + fusion).

    The explanation layer is applied separately by the caller so that scans
    still succeed when the LLM is unavailable.
    """
    rule_score, flags = rules.evaluate(text)
    clf_prob = classifier.scam_probability(text)
    score, confidence = fuse(clf_prob, rule_score)

    return RiskReport(
        risk_level=level_for(score),
        risk_score=score,
        confidence=confidence,
        classifier_probability=clf_prob,
        rule_score=rule_score,
        flags=[f.to_dict() for f in flags],
    )
