from app.services.pipeline import analyze, fuse, level_for


def test_fuse_without_classifier_uses_rules():
    score, confidence = fuse(None, 0.8)
    assert score == 0.8
    assert confidence == 0.5


def test_fuse_agreement_high_confidence():
    score, confidence = fuse(0.95, 0.9)
    assert score > 0.85
    assert confidence > 0.8


def test_fuse_one_strong_signal_carries():
    # Classifier is sure, rules found nothing (e.g. novel scam wording)
    score, _ = fuse(0.99, 0.0)
    assert score >= 0.85
    # Rules are sure, classifier missed (e.g. out-of-distribution channel)
    score, _ = fuse(0.05, 0.95)
    assert score >= 0.8


def test_fuse_bounded():
    score, confidence = fuse(1.0, 1.0)
    assert score <= 1.0
    assert confidence <= 1.0


def test_level_thresholds():
    assert level_for(0.9) == "high"
    assert level_for(0.65) == "high"
    assert level_for(0.5) == "medium"
    assert level_for(0.3) == "medium"
    assert level_for(0.1) == "low"


def test_analyze_scam_end_to_end():
    report = analyze(
        "URGENT: Your Chase account is locked. Verify your identity at "
        "chase-secure-verify.tk or your account will be permanently closed. "
        "Pay the reactivation fee with gift cards."
    )
    assert report.risk_level == "high"
    assert report.risk_score > 0.65
    assert len(report.flags) >= 3
    assert report.classifier_probability is not None


def test_analyze_benign_end_to_end():
    report = analyze("Reminder: dentist appointment Tuesday at 2:30 PM. "
                     "Reply C to confirm.")
    assert report.risk_level == "low"
