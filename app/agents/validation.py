from __future__ import annotations

import re
import time

from app.models.agent_state import ClaimWorkflowState
from app.models.decision import TraceEvent, ValidationResult
from app.services.confidence import decision_confidence


class ValidationAgent:
    name = "ValidationAgent"

    def run(self, state: ClaimWorkflowState) -> ClaimWorkflowState:
        started = time.perf_counter()
        assert state.decision_draft is not None
        evidence = {item.chunk_id: item for item in state.retrieved_evidence}
        invalid, unsupported, numeric = [], [], []
        cited_claims = {citation.claim for citation in state.decision_draft.citations}
        for citation in state.decision_draft.citations:
            item = evidence.get(citation.chunk_id)
            if not item or item.page != citation.page or item.section != citation.section or item.source != citation.source:
                invalid.append(citation.chunk_id)
                continue
            claim_terms = set(re.findall(r"[a-z]{4,}", citation.claim.lower())) - {"with", "that", "this", "when", "from", "into", "subject", "policy"}
            evidence_terms = set(re.findall(r"[a-z]{4,}", item.text.lower()))
            if claim_terms and len(claim_terms & evidence_terms) / len(claim_terms) < 0.1:
                unsupported.append(citation.claim)
        for finding in state.specialist_findings:
            if finding.status != "UNCERTAIN" and finding.finding not in cited_claims:
                unsupported.append(finding.finding)
            numbers = re.findall(r"\b(?:20|25|30|40|48|60)\b", finding.finding)
            if numbers and finding.evidence_chunk_ids:
                texts = " ".join(evidence[cid].text for cid in finding.evidence_chunk_ids if cid in evidence)
                if any(number not in texts for number in numbers):
                    numeric.append(finding.finding)
        fail = bool(invalid or unsupported or numeric)
        result = ValidationResult(status="FAIL" if fail else "PASS", unsupported_claims=unsupported,
            invalid_citations=invalid, numeric_mismatches=numeric, revision_required=fail)
        state.validation = result
        state.decision_draft.validation = result
        state.decision_draft.confidence = decision_confidence(evidence_count=len(state.decision_draft.citations),
            uncertain_findings=sum(item.status == "UNCERTAIN" for item in state.specialist_findings), validation_passed=not fail)
        state.trace.append(TraceEvent(agent=self.name, action="validate_claims_citations_and_numbers", elapsed_ms=(time.perf_counter()-started)*1000,
            brief_outcome=result.status, retry_count=state.retry_count))
        return state
