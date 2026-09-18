from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DecisionStatus = Literal[
    "ADMISSIBLE", "ADMISSIBLE_WITH_LIMITS", "PARTIALLY_ADMISSIBLE", "NOT_ADMISSIBLE", "NEEDS_REVIEW"
]


class Citation(BaseModel):
    claim: str
    source: str
    page: int
    section: str
    chunk_id: str
    excerpt: str


class Finding(BaseModel):
    finding_id: str
    dimension: str
    finding: str
    status: Literal["SUPPORTED", "NOT_SUPPORTED", "UNCERTAIN"]
    evidence_chunk_ids: list[str]
    policy_pages: list[int]
    certainty: float = Field(ge=0, le=1)
    missing_evidence: list[str] = []


class ValidationResult(BaseModel):
    status: Literal["PASS", "FAIL"]
    unsupported_claims: list[str] = []
    invalid_citations: list[str] = []
    numeric_mismatches: list[str] = []
    revision_required: bool = False


class TraceEvent(BaseModel):
    agent: str
    action: str
    elapsed_ms: float
    brief_outcome: str
    retrieval_query: str | None = None
    result_count: int | None = None
    evidence_ids: list[str] = []
    retry_count: int = 0


class ClaimDecision(BaseModel):
    case_id: str
    decision: DecisionStatus
    confidence: float = Field(ge=0, le=1)
    key_findings: list[Finding]
    applicable_limits: list[dict]
    deductions: list[dict]
    estimated_payable_inr: float | None = None
    missing_evidence: list[str]
    citations: list[Citation]
    next_action: str
    reason_code: str | None = None
    validation: ValidationResult
    trace: list[TraceEvent]
    disclaimer: str = "Prototype decision support only; formal claim adjudication remains with the insurer."
