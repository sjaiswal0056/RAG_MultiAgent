from __future__ import annotations

import time
from collections.abc import Iterable

from app.models.agent_state import ClaimWorkflowState
from app.models.decision import Finding, TraceEvent
from app.models.evidence import Evidence


def _select(evidence: Iterable[Evidence], terms: tuple[str, ...], dimension: str | None = None) -> list[Evidence]:
    ranked = []
    for item in evidence:
        text = f"{item.section} {item.heading} {item.text}".lower()
        score = sum(term.lower() in text for term in terms) + (2 if dimension and item.dimension == dimension else 0)
        if score:
            ranked.append((score, item.rerank_score, item))
    ranked.sort(key=lambda row: (-row[0], -row[1]))
    unique = []
    seen = set()
    for _, _, item in ranked:
        if item.chunk_id not in seen:
            unique.append(item)
            seen.add(item.chunk_id)
    return unique[:2]


class CoverageExclusionAgent:
    name = "CoverageExclusionAgent"

    def run(self, state: ClaimWorkflowState) -> ClaimWorkflowState:
        started = time.perf_counter()
        case, evidence = state.case, state.retrieved_evidence
        treatment_text = f"{case.treatment.diagnosis} {case.treatment.procedure}".lower()
        findings: list[Finding] = []

        def add(dimension: str, text: str, status: str, terms: tuple[str, ...], missing: list[str] | None = None) -> None:
            support = _select(evidence, terms, dimension)
            findings.append(Finding(
                finding_id=f"F-{len(findings)+1:03d}", dimension=dimension, finding=text, status=status,
                evidence_chunk_ids=[item.chunk_id for item in support], policy_pages=sorted({item.page for item in support}),
                certainty=0.9 if support and status != "UNCERTAIN" else 0.35, missing_evidence=missing or [],
            ))

        add("coverage", "The policy covers reasonable and customary hospitalization expenses when hospitalization is medically advised.",
            "SUPPORTED", ("what we cover", "hospitalization expenses", "reasonable and customary"))
        context = case.evidence_context or {}
        hospital_gap = context.get("hospital_registered") is None and context.get("hospital_minimum_criteria_documented") is False
        if hospital_gap:
            add("hospital_eligibility", "The supplied case evidence does not establish that the facility meets the policy definition of a Hospital.",
                "UNCERTAIN", ("hospital means", "minimum criteria", "registered"), ["Hospital registration or minimum-criteria evidence"])
        else:
            add("hospital_eligibility", "The policy requires a Hospital to be registered or meet its minimum criteria; the case identifies a network provider and no contrary evidence.",
                "SUPPORTED", ("hospital means", "registered", "minimum criteria"))

        if "medical_necessity_confirmed" in context and context.get("medical_necessity_confirmed") is None:
            add("required_evidence", "Medical necessity is not established by the supplied evidence.", "UNCERTAIN",
                ("medically necessary", "medical practitioner", "evidences"), ["Medical-necessity confirmation"])

        if (case.claim_date - case.policy_start_date).days < 30 and case.prior_insurer_continuous_years < 1:
            add("initial_waiting_period", "The claim falls within the 30-day waiting period and no qualifying prior continuous year is shown.",
                "NOT_SUPPORTED", ("30 days waiting period", "at least 1 year", "continuously"))

        listed_first_year = ("cataract", "hernia", "hydrocele", "fistula", "piles", "arthritis", "gout", "rheumatism", "sinusitis", "stone", "tonsil", "ulcer")
        is_listed = any(term in treatment_text for term in listed_first_year)
        if case.continuous_coverage_months < 12 and is_listed:
            prior = case.prior_policy or {}
            waived = case.prior_insurer_continuous_years >= 1 and bool(prior.get("database_and_claim_history_received"))
            add("disease_specific_waiting", "The first-year disease-specific waiting period applies unless one completed prior continuous year and required records support waiver.",
                "SUPPORTED" if waived else "NOT_SUPPORTED", ("first year", "cataract", "at least 1 year", "database and claim history"))

        if case.treatment.pre_existing:
            credited_months = case.continuous_coverage_months + 12 * case.prior_insurer_continuous_years
            if credited_months < 48:
                add("pre_existing", f"The pre-existing disease waiting period is not exhausted ({credited_months} credited months versus 48 months).",
                    "NOT_SUPPORTED", ("pre-existing diseases", "48 months", "reduced"))
            else:
                add("pre_existing", "The credited continuous coverage meets the 48-month pre-existing disease waiting period.",
                    "SUPPORTED", ("pre-existing diseases", "48 months", "continuous"))

        if case.treatment.experimental:
            add("experimental_exclusion", "The case identifies the treatment as experimental/unproven, which is outside supported approved treatment.",
                "NOT_SUPPORTED", ("unproven", "experimental", "not approved"))
        if "cosmetic" in treatment_text or "aesthetic" in treatment_text:
            add("cosmetic_exclusion", "Cosmetic or aesthetic treatment is excluded unless a policy exception is established; none is supplied.",
                "NOT_SUPPORTED", ("cosmetic", "aesthetic", "plastic surgery"))

        if case.treatment.type.lower() == "day_care" or case.treatment.admission_hours < 24:
            listed = any(word in treatment_text for word in ("eye surgery", "cataract", "dialysis", "chemotherapy", "radiotherapy", "lithotripsy", "tonsillectomy"))
            status = "SUPPORTED" if listed else "UNCERTAIN"
            missing = [] if listed else ["Evidence that the sub-24-hour procedure meets the policy's day-care conditions"]
            add("day_care", "A sub-24-hour procedure may qualify where it is a specified treatment or meets the technological-advancement conditions.",
                status, ("less than 24", "day care treatment", "eye surgery", "technological advances"), missing)

        if case.treatment.type.lower() == "domiciliary":
            home_condition = bool(getattr(case.treatment, "hospital_room_unavailable", False) or getattr(case.treatment, "patient_cannot_be_moved", False))
            duration = getattr(case.treatment, "treatment_days", None)
            if not home_condition:
                add("domiciliary", "The required home-treatment circumstance is not established.", "NOT_SUPPORTED",
                    ("domiciliary", "non-availability of room", "not in a condition"))
            elif duration is None:
                add("domiciliary", "The supplied facts show a qualifying home-treatment circumstance under the domiciliary treatment definition.",
                    "SUPPORTED", ("domiciliary treat", "non-availability of room", "not in a condition"))
                add("domiciliary", "The policy excludes treatment not exceeding three days, but the domiciliary treatment duration is missing.",
                    "UNCERTAIN", ("not exceeding three days",), ["Domiciliary treatment duration"])
            else:
                add("domiciliary", "The supplied facts satisfy the home-treatment circumstance and duration requirements.", "SUPPORTED",
                    ("domiciliary", "three days", "20%"))
            add("domiciliary", "Domiciliary hospitalization expense is limited to 20% of Basic Sum Insured.",
                "SUPPORTED", ("domiciliary hospitalization", "20%"))

        if case.prior_insurer_continuous_years >= 1:
            prior = case.prior_policy or {}
            complete = bool(prior.get("database_and_claim_history_received"))
            add("portability", "One completed prior continuous year may reduce applicable waiting periods when required prior-insurer records are received.",
                "SUPPORTED" if complete else "UNCERTAIN", ("at least 1 year", "database and claim history", "portability"),
                [] if complete else ["Previous insurer database and claim history"])

        add("expense_limits", "Normal room expense is limited to 1% of Basic Sum Insured per day.",
            "SUPPORTED", ("normal room expenses", "1.0%"))
        add("expense_limits", "Medical practitioner, consultant, anesthetist, and surgeon fees are limited to 25% of Sum Insured.",
            "SUPPORTED", ("25%", "surgeons fees", "consultant fees"))
        add("expense_limits", "Medicines, diagnostics, operation theatre and similar listed expenses are limited to 40% of Sum Insured.",
            "SUPPORTED", ("40%", "diagnostic materials", "medicines and drugs"))
        add("expense_limits", "Ambulance expense for an admissible claim is limited to the lower of 1% of Basic Sum Insured or INR 1,000.",
            "SUPPORTED", ("ambulance charges", "1000", "1.0%"))
        if case.expense_timing:
            add("expense_windows", "Pre-hospitalization is limited to 30 days and post-hospitalization to 60 days, for the same condition and an admissible inpatient claim.",
                "SUPPORTED", ("30 days", "60 days", "pre-hospitalisation", "post hospitalisation"))
        state.specialist_findings = findings
        state.trace.append(TraceEvent(agent=self.name, action="apply_policy_evidence_contract", elapsed_ms=(time.perf_counter()-started)*1000,
            evidence_ids=sorted({item for finding in findings for item in finding.evidence_chunk_ids}), brief_outcome=f"Produced {len(findings)} grounded findings"))
        return state
