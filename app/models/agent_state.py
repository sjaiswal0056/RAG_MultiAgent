from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.claim import ClaimCase
from app.models.decision import ClaimDecision, Finding, TraceEvent, ValidationResult
from app.models.evidence import Evidence


class RetrievalQuery(BaseModel):
    dimension: str
    query: str


class CaseAnalysisOutput(BaseModel):
    facts: dict
    relevant_dimensions: list[str]
    missing_fields: list[str]
    retrieval_queries: list[RetrievalQuery]
    investigation_checklist: list[str]


class ClaimWorkflowState(BaseModel):
    case: ClaimCase
    analysis: CaseAnalysisOutput | None = None
    retrieved_evidence: list[Evidence] = []
    specialist_findings: list[Finding] = []
    decision_draft: ClaimDecision | None = None
    validation: ValidationResult | None = None
    trace: list[TraceEvent] = []
    errors: list[str] = []
    retry_count: int = 0
