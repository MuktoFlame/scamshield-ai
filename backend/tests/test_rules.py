from app.services.rules import evaluate


def flag_ids(text):
    _, flags = evaluate(text)
    return {f.id for f in flags}


def test_benign_text_scores_near_zero():
    score, flags = evaluate("Hey, are we still on for lunch tomorrow at noon?")
    assert score < 0.1
    assert flags == []


def test_gift_card_demand_flagged():
    ids = flag_ids("Please buy $500 in Apple gift cards and send the codes.")
    assert "untraceable_payment" in ids


def test_urgency_and_threat_flagged():
    ids = flag_ids("URGENT: your account will be suspended within 24 hours!")
    assert "urgency" in ids
    assert "threat" in ids


def test_credential_request_flagged():
    ids = flag_ids("Please verify your identity and enter your PIN to continue.")
    assert "credential_request" in ids


def test_lookalike_domain_flagged():
    ids = flag_ids("Update billing at netfIix-billing-update.com today")
    assert "lookalike_domain" in ids


def test_shortener_flagged():
    ids = flag_ids("Click here to claim: bit.ly/3xYzAbC")
    assert "shortened_url" in ids


def test_ip_url_flagged():
    ids = flag_ids("Login at http://192.168.4.12/secure to restore access")
    assert "ip_url" in ids


def test_secrecy_flagged():
    ids = flag_ids("It's me, don't tell mom and dad. I can't talk right now.")
    assert "secrecy" in ids


def test_advance_fee_flagged():
    ids = flag_ids("Send the $150 processing fee to release your winnings.")
    assert "advance_fee" in ids


def test_reward_bait_flagged():
    ids = flag_ids("Congratulations, you have won the national lottery jackpot")
    assert "too_good" in ids


def test_score_accumulates_and_stays_bounded():
    score, flags = evaluate(
        "URGENT! You won $2 million! Verify your PIN and pay the processing "
        "fee with gift cards NOW! Your account will be suspended! Call this "
        "number immediately!!!"
    )
    assert len(flags) >= 5
    assert 0.9 <= score <= 1.0


def test_evidence_is_captured():
    _, flags = evaluate("Buy iTunes card now, wire transfer also accepted")
    payment = next(f for f in flags if f.id == "untraceable_payment")
    assert any("itunes" in e.lower() for e in payment.evidence)
