from __future__ import annotations

import time

from app.models.agent_state import ClaimWorkflowState
from app.models.decision import Citation, ClaimDecision, TraceEvent, ValidationResult
from app.services.confidence import decision_confidence
from app.services.limit_calculator import calculate_limits


class DecisionAgent:
    name = "DecisionAgent"

    def run(self, state: ClaimWorkflowState) -> ClaimWorkflowState:
        started = time.perf_counter()
        findings = state.specialist_findings
        uncertain = [item for item in findings if item.status == "UNCERTAIN"]
        blockers = [item for item in findings if item.status == "NOT_SUPPORTED"]
        missing = sorted({value for item in findings for value in item.missing_evidence})
        evidence_map = {item.chunk_id: item for item in state.retrieved_evidence}
        citations = []
        for finding in findings:
            for chunk_id in finding.evidence_chunk_ids[:1]:
                item = evidence_map.get(chunk_id)
                if item:
                    citations.append(Citation(claim=finding.finding, source=item.source, page=item.page, section=item.section,
                        chunk_id=item.chunk_id, excerpt=item.text[:360]))
        if uncertain:
            status, reason, next_action = "NEEDS_REVIEW", "INSUFFICIENT_EVIDENCE", "Obtain the listed missing evidence and rerun the analysis."
            limits, deductions, payable = [], [], None
        elif blockers:
            status, reason, next_action = "NOT_ADMISSIBLE", "POLICY_EXCLUSION_OR_WAITING_PERIOD", "Route for formal insurer review with the cited policy clauses."
            limits, deductions, payable = [], [], 0.0
        else:
            domicile = state.case.treatment.type.lower() == "domiciliary"
            limits, deductions, payable = calculate_limits(state.case, domicile)
            status = "ADMISSIBLE_WITH_LIMITS" if limits or deductions else "ADMISSIBLE"
            reason, next_action = "POLICY_SUPPORTED_WITH_LIMITS", "Verify originals and settle subject to policy terms and remaining sum insured."
        draft_validation = ValidationResult(status="FAIL", revision_required=True)
        confidence = decision_confidence(evidence_count=len(citations), uncertain_findings=len(uncertain), validation_passed=False)
        state.decision_draft = ClaimDecision(case_id=state.case.case_id, decision=status, confidence=confidence,
            key_findings=findings, applicable_limits=limits, deductions=deductions, estimated_payable_inr=payable,
            missing_evidence=missing, citations=citations, next_action=next_action, reason_code=reason,
            validation=draft_validation, trace=[])
        state.trace.append(TraceEvent(agent=self.name, action="synthesize_structured_decision", elapsed_ms=(time.perf_counter()-started)*1000,
            evidence_ids=[item.chunk_id for item in citations], brief_outcome=f"Drafted {status}", retry_count=state.retry_count))
        return state
