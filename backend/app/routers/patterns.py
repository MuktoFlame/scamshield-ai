"""Curated scam-pattern education library served to the Learn page."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["patterns"])

PATTERNS = [
    {
        "id": "bank_impersonation",
        "title": "Fake bank alerts",
        "example": "URGENT: Your account has been locked. Verify your identity at chase-secure-verify.com",
        "how_it_works": "The message copies a real bank's tone and logo, then links to a fake login page that steals your password and card details.",
        "how_to_respond": "Never use the link or number in the message. Call the number printed on the back of your card instead.",
    },
    {
        "id": "tech_support",
        "title": "Tech support scams",
        "example": "This is Microsoft Support. We detected a virus on your computer. Call us immediately.",
        "how_it_works": "The caller creates panic about a virus, then asks for remote access to your computer or payment for fake repairs.",
        "how_to_respond": "Microsoft, Apple and Google never call you about viruses. Hang up. If worried, ask a family member to check your device.",
    },
    {
        "id": "grandparent",
        "title": "Family emergency / 'Hi mom' scams",
        "example": "Grandma it's me, I'm in trouble. I need gift cards urgently. Don't tell mom and dad.",
        "how_it_works": "The scammer pretends to be a relative in urgent trouble on a new number, and asks for secrecy so you can't check.",
        "how_to_respond": "Hang up and call the relative on their usual number. A real emergency survives a two-minute check.",
    },
    {
        "id": "delivery",
        "title": "Fake delivery notices",
        "example": "Your package could not be delivered. Pay a $1.99 customs fee: usps-redelivery.info",
        "how_it_works": "The tiny 'fee' is bait — the real goal is your card number, which is then used for much larger charges.",
        "how_to_respond": "Track packages only on the courier's official website or app, typed in yourself.",
    },
    {
        "id": "prize",
        "title": "Lottery and prize scams",
        "example": "Congratulations! You've won $2,500,000. Send a $150 processing fee to claim.",
        "how_it_works": "You are asked to pay a small fee to unlock a large prize. The prize never existed; they keep the fee and ask for more.",
        "how_to_respond": "If you didn't enter, you didn't win. Real prizes never require payment to receive.",
    },
    {
        "id": "government",
        "title": "IRS / government threats",
        "example": "A warrant has been issued for your arrest. Pay immediately via gift cards to cancel it.",
        "how_it_works": "Fear of arrest or legal trouble pushes people to pay instantly. Government agencies never take gift cards or threaten arrest by phone.",
        "how_to_respond": "Hang up. Government agencies contact you by official mail and never demand instant payment.",
    },
    {
        "id": "romance",
        "title": "Romance scams",
        "example": "I feel a deep connection with you. Could you help me with a small transfer fee? I'll pay you back double.",
        "how_it_works": "After weeks of warm messages, an 'emergency' appears that only your money can fix. The person and the emergency are both fake.",
        "how_to_respond": "Never send money to someone you haven't met in person, no matter how long you've been talking.",
    },
    {
        "id": "boss_giftcard",
        "title": "Boss / coworker gift-card requests",
        "example": "I'm in a meeting and can't call. Buy 3 gift cards for a client and send me the codes. - Your Boss",
        "how_it_works": "The scammer poses as your boss with an urgent, confidential task. Gift-card codes are cash that can't be recovered.",
        "how_to_respond": "Verify in person or by calling your boss's known number. No real manager asks for gift cards by text.",
    },
]


@router.get("/patterns")
def list_patterns():
    return {"patterns": PATTERNS}
