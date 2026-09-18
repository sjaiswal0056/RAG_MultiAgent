from app.agents.validation import ValidationAgent
from app.models.agent_state import ClaimWorkflowState
from app.models.claim import ClaimCase
from app.models.decision import Citation, ClaimDecision, Finding, ValidationResult


def test_invalid_chunk_id_fails_validation(public_cases):
    finding = Finding(finding_id="F", dimension="coverage", finding="A material claim", status="SUPPORTED",
        evidence_chunk_ids=["missing"], policy_pages=[1], certainty=0.9)
    decision = ClaimDecision(case_id="PUB-001", decision="ADMISSIBLE", confidence=0.5, key_findings=[finding],
        applicable_limits=[], deductions=[], missing_evidence=[], citations=[Citation(claim=finding.finding, source="p", page=1, section="s", chunk_id="missing", excerpt="x")],
        next_action="x", validation=ValidationResult(status="FAIL"), trace=[])
    state = ClaimWorkflowState(case=ClaimCase.model_validate(public_cases[0]), specialist_findings=[finding], decision_draft=decision)
    result = ValidationAgent().run(state)
    assert result.validation.status == "FAIL"
    assert "missing" in result.validation.invalid_citations
