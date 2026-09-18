def decision_confidence(*, evidence_count: int, uncertain_findings: int, validation_passed: bool) -> float:
    score = 0.55 + min(evidence_count, 10) * 0.025 - uncertain_findings * 0.15
    if validation_passed:
        score += 0.12
    return round(max(0.05, min(score, 0.95)), 2)
