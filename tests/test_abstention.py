from app.models.claim import ClaimCase


def test_missing_hospital_evidence_abstains(workflow, public_cases):
    result = workflow.analyze(ClaimCase.model_validate(public_cases[10]))
    assert result.decision == "NEEDS_REVIEW"
    assert result.reason_code == "INSUFFICIENT_EVIDENCE"
