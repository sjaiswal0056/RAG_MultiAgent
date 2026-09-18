from __future__ import annotations

from app.agents import CaseAnalysisAgent, CoverageExclusionAgent, DecisionAgent, PolicyEvidenceAgent, ValidationAgent
from app.config import settings
from app.models.agent_state import ClaimWorkflowState
from app.models.claim import ClaimCase
from app.models.decision import ClaimDecision, TraceEvent
from app.retrieval.hybrid_retriever import HybridRetriever


class ClaimWorkflow:
    def __init__(self, retriever: HybridRetriever):
        self.case_agent = CaseAnalysisAgent()
        self.evidence_agent = PolicyEvidenceAgent(retriever)
        self.coverage_agent = CoverageExclusionAgent()
        self.decision_agent = DecisionAgent()
        self.validation_agent = ValidationAgent()

    def analyze(self, case: ClaimCase) -> ClaimDecision:
        state = ClaimWorkflowState(case=case)
        for agent in (self.case_agent, self.evidence_agent, self.coverage_agent, self.decision_agent, self.validation_agent):
            state = agent.run(state)
        while state.validation and state.validation.status == "FAIL" and state.retry_count < settings.max_validation_retries:
            state.retry_count += 1
            state = self.decision_agent.run(state)
            state = self.validation_agent.run(state)
        assert state.decision_draft is not None
        if state.validation and state.validation.status == "FAIL":
            state.decision_draft.decision = "NEEDS_REVIEW"
            state.decision_draft.reason_code = "VALIDATION_FAILED"
            state.decision_draft.estimated_payable_inr = None
            state.decision_draft.next_action = "A human reviewer must resolve unsupported claims or citation mismatches."
            state.decision_draft.missing_evidence = sorted(set(state.decision_draft.missing_evidence + state.validation.unsupported_claims))
        state.decision_draft.trace = state.trace
        return state.decision_draft
