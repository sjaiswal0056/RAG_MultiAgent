from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FlexibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class Patient(FlexibleModel):
    age: int = Field(ge=0, le=130)


class Hospital(FlexibleModel):
    name: str = Field(min_length=1)
    network_provider: bool | None = None


class Treatment(FlexibleModel):
    type: str = Field(min_length=1)
    admission_hours: float = Field(ge=0)
    diagnosis: str = Field(min_length=1)
    procedure: str = Field(min_length=1)
    pre_existing: bool
    experimental: bool


class Expenses(FlexibleModel):
    room: float = Field(default=0, ge=0)
    doctor_fees: float = Field(default=0, ge=0)
    medicines_diagnostics: float = Field(default=0, ge=0)
    pre_hospitalization: float = Field(default=0, ge=0)
    post_hospitalization: float = Field(default=0, ge=0)
    ambulance: float = Field(default=0, ge=0)


class ClaimCase(FlexibleModel):
    case_id: str = Field(min_length=1)
    policy_id: str = Field(min_length=1)
    policy_start_date: date
    claim_date: date
    sum_insured_inr: float = Field(gt=0)
    continuous_coverage_months: int = Field(ge=0)
    prior_insurer_continuous_years: int = Field(ge=0)
    patient: Patient
    hospital: Hospital
    treatment: Treatment
    expenses_inr: Expenses
    documents: list[str]
    task: str = Field(min_length=1)
    prior_policy: dict[str, Any] | None = None
    evidence_context: dict[str, Any] | None = None
    expense_timing: dict[str, Any] | None = None

    @field_validator("claim_date")
    @classmethod
    def claim_not_before_policy(cls, value: date, info: Any) -> date:
        start = info.data.get("policy_start_date")
        if start and value < start:
            raise ValueError("claim_date must not precede policy_start_date")
        return value
