import pytest
from pydantic import ValidationError

from app.models.claim import ClaimCase


def test_valid_public_case_and_extra_field(public_cases):
    raw = dict(public_cases[0])
    raw["reviewer_note"] = "ignored but retained"
    model = ClaimCase.model_validate(raw)
    assert model.case_id == "PUB-001"
    assert model.reviewer_note == "ignored but retained"


def test_malformed_case_rejected(public_cases):
    raw = dict(public_cases[0])
    raw.pop("policy_id")
    with pytest.raises(ValidationError):
        ClaimCase.model_validate(raw)
