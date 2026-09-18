from __future__ import annotations

import math

from app.models.claim import ClaimCase


def calculate_limits(case: ClaimCase, domiciliary: bool = False) -> tuple[list[dict], list[dict], float]:
    si = case.sum_insured_inr
    expenses = case.expenses_inr
    days = max(1, math.ceil(case.treatment.admission_hours / 24))
    limits = [
        {"category": "normal_room_per_day", "rule": "1% of Basic Sum Insured", "amount_inr": 0.01 * si},
        {"category": "practitioner_and_surgeon_fees", "rule": "25% of Sum Insured", "amount_inr": 0.25 * si},
        {"category": "medicines_diagnostics_and_similar", "rule": "40% of Sum Insured", "amount_inr": 0.40 * si},
        {"category": "ambulance_per_claim", "rule": "lower of 1% of Basic Sum Insured or INR 1,000", "amount_inr": min(0.01 * si, 1000)},
    ]
    allowed = {
        "room": min(expenses.room, 0.01 * si * days),
        "doctor_fees": min(expenses.doctor_fees, 0.25 * si),
        "medicines_diagnostics": min(expenses.medicines_diagnostics, 0.40 * si),
        "pre_hospitalization": expenses.pre_hospitalization,
        "post_hospitalization": expenses.post_hospitalization,
        "ambulance": min(expenses.ambulance, 0.01 * si, 1000),
    }
    timing = case.expense_timing or {}
    if timing:
        if timing.get("pre_hospitalization_days_before_admission", 0) > 30 or not timing.get("same_condition_confirmed", False):
            allowed["pre_hospitalization"] = 0
        if timing.get("post_hospitalization_days_after_discharge", 0) > 60 or not timing.get("same_condition_confirmed", False):
            allowed["post_hospitalization"] = 0
    gross = sum(case.expenses_inr.model_dump().values())
    payable = min(sum(allowed.values()), si)
    if domiciliary:
        domicile_cap = 0.20 * si
        limits.append({"category": "domiciliary_hospitalization", "rule": "20% of Basic Sum Insured", "amount_inr": domicile_cap})
        payable = min(payable, domicile_cap)
    deductions = []
    for category, billed in case.expenses_inr.model_dump().items():
        reduction = billed - allowed.get(category, billed)
        if reduction > 0:
            deductions.append({"category": category, "billed_inr": billed, "allowed_inr": allowed[category], "deduction_inr": reduction})
    if gross > si:
        deductions.append({"category": "overall_sum_insured", "billed_inr": gross, "allowed_inr": si, "deduction_inr": gross - si})
    return limits, deductions, round(payable, 2)
