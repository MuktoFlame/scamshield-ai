"""Heuristic rule engine: explainable, deterministic scam indicators.

Each rule that fires produces a Flag with the matched evidence text, a severity
weight, and a plain-language description a non-technical reader can understand.
The aggregate rule score feeds the fusion step alongside the ML classifier.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

from .url_features import find_url_findings_in_text


@dataclass
class Flag:
    id: str
    title: str
    description: str
    severity: float  # 0..1, contribution weight
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

# (pattern, evidence-friendly) rule definitions
URGENCY_PATTERNS = re.compile(
    r"\b(urgent(ly)?|immediately|right now|act now|expires? (today|soon|in \d+)|"
    r"within \d+ (hours?|minutes?)|final (notice|warning|reminder)|last chance|"
    r"asap|don'?t delay|time.?sensitive|before it'?s too late|24 hours?)\b", re.I)

PAYMENT_PATTERNS = re.compile(
    r"\b(gift ?cards?|itunes card|google play card|steam card|western union|"
    r"moneygram|wire transfer|crypto(currency)?|bitcoin|btc|usdt|ethereum|"
    r"prepaid (card|debit)|money order|cash ?app|zelle|venmo)\b", re.I)

CREDENTIAL_PATTERNS = re.compile(
    r"\b(verify your (identity|account|information|details)|confirm your "
    r"(identity|account|password|pin|ssn)|enter your pin|one.?time password|"
    r"otp|social security (number)?|log ?in (details|credentials)|"
    r"update your (billing|payment|account) (info|information|details)|"
    r"(send|share|provide) (me |us )?your (password|pin|bank details|card number))\b", re.I)

IMPERSONATION_PATTERNS = re.compile(
    r"\b(this is (the )?(irs|microsoft|apple|amazon|your bank|google) (support|security|team)?|"
    r"(bank|security|fraud) (alert|department|team)|tech(nical)? support|"
    r"government (grant|refund)|tax (refund|department)|social security administration|"
    r"customs (fee|department)|delivery (fee|attempt|failed))\b", re.I)

THREAT_PATTERNS = re.compile(
    r"\b(account (will be |is )?(suspended|locked|closed|deactivated|terminated)|"
    r"legal action|arrest(ed)? (warrant)?|warrant (has been )?issued|lawsuit|"
    r"police|disconnect(ed|ion)?|suspended|permanently (closed|deleted|lost))\b", re.I)

REWARD_PATTERNS = re.compile(
    r"\b(congratulations|you('ve| have)? (won|been selected|been chosen)|winner|"
    r"lottery|prize|jackpot|claim your (reward|prize|grant|refund|money)|"
    r"free (gift|money|iphone|vacation)|\$\d[\d,.]*\s*(million|m\b)|inheritance|"
    r"unclaimed (funds?|money)|giving away)\b", re.I)

SECRECY_PATTERNS = re.compile(
    r"\b(don'?t tell (anyone|mom|dad|your family)|keep (this|it) (a secret|between us|"
    r"confidential)|do not (contact|inform|tell)|can'?t talk right now|"
    r"new (number|phone),? (this is|it'?s) (me|my))\b", re.I)

CALLBACK_PATTERNS = re.compile(
    r"\b(call (us |our |this number |now |immediately )|press [0-9]|dial \*?\d)", re.I)

FEE_ADVANCE_PATTERNS = re.compile(
    r"\b((processing|release|registration|activation|transfer|customs|admin(istration)?)"
    r" fee|small (fee|payment|transfer)|pay (a )?fee|upfront (payment|fee|cost)|"
    r"reimburse|pay you back (double|twice))\b", re.I)


def _find(pattern: re.Pattern, text: str, limit: int = 4) -> list[str]:
    seen: list[str] = []
    for m in pattern.finditer(text):
        ev = m.group(0).strip()
        if ev.lower() not in (s.lower() for s in seen):
            seen.append(ev)
        if len(seen) >= limit:
            break
    return seen


def _check_urls(text: str) -> list[Flag]:
    return [Flag(**f) for f in find_url_findings_in_text(text)]


RULES: list[tuple[re.Pattern, Flag]] = [
    (URGENCY_PATTERNS, Flag(
        "urgency", "Pressure to act immediately",
        "The message pushes you to act right away. Creating panic so you don't "
        "stop to think is the single most common scam tactic.", 0.55)),
    (PAYMENT_PATTERNS, Flag(
        "untraceable_payment", "Asks for hard-to-trace payment",
        "Gift cards, wire transfers and cryptocurrency are favored by scammers "
        "because payments cannot be reversed. No legitimate business or agency "
        "demands them.", 0.9)),
    (CREDENTIAL_PATTERNS, Flag(
        "credential_request", "Asks for passwords, PINs or personal details",
        "It asks you to 'verify' or hand over sensitive information. Real banks "
        "and companies never ask for passwords, PINs or full card numbers by "
        "message.", 0.85)),
    (IMPERSONATION_PATTERNS, Flag(
        "impersonation", "Claims to be a bank, agency or big company",
        "The sender claims to represent a trusted organization. Scammers "
        "impersonate banks, tax agencies and delivery services to borrow their "
        "credibility.", 0.6)),
    (THREAT_PATTERNS, Flag(
        "threat", "Threatens bad consequences",
        "It threatens account closure, arrest, disconnection or legal trouble. "
        "Real organizations do not threaten you by text or email.", 0.7)),
    (REWARD_PATTERNS, Flag(
        "too_good", "Promises money or prizes",
        "It promises winnings, inheritance or free money. If you did not enter "
        "a lottery, you did not win one.", 0.7)),
    (SECRECY_PATTERNS, Flag(
        "secrecy", "Asks for secrecy or claims a new number",
        "Asking you to keep things secret, or claiming to be a family member on "
        "a new number, is designed to stop you from checking with anyone.", 0.85)),
    (CALLBACK_PATTERNS, Flag(
        "callback", "Urges you to call a number or press a key",
        "It pushes you to call an unknown number or press a key. That connects "
        "you to the scammer's own call center, not the real company.", 0.45)),
    (FEE_ADVANCE_PATTERNS, Flag(
        "advance_fee", "Asks for an upfront fee to unlock money",
        "You are asked to pay a small fee to receive a much larger amount. The "
        "larger amount does not exist — only the fee is real.", 0.8)),
]


def evaluate(text: str) -> tuple[float, list[Flag]]:
    """Run every rule. Returns (rule_score 0..1, flags)."""
    flags: list[Flag] = []

    for pattern, template in RULES:
        evidence = _find(pattern, text)
        if evidence:
            flags.append(Flag(template.id, template.title,
                              template.description, template.severity, evidence))

    flags.extend(_check_urls(text))

    letters = [c for c in text if c.isalpha()]
    if len(letters) >= 30:
        caps_ratio = sum(c.isupper() for c in letters) / len(letters)
        if caps_ratio > 0.5:
            flags.append(Flag(
                "shouting", "Excessive capital letters",
                "Large parts of the message are written in capitals to create "
                "alarm — a common trait of scam messages.", 0.3,
                [f"{caps_ratio:.0%} of letters are capitalized"]))
    if text.count("!") >= 3:
        flags.append(Flag(
            "exclamation", "Excessive punctuation",
            "Repeated exclamation marks are used to create excitement or panic.",
            0.2, [f"{text.count('!')} exclamation marks"]))

    # Aggregate: 1 - prod(1 - severity). One strong flag dominates; several
    # weak flags accumulate. Bounded to [0, 1].
    score = 1.0
    for f in flags:
        score *= (1.0 - f.severity)
    return round(1.0 - score, 4), flags
