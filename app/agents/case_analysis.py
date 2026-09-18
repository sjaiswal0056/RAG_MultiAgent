from __future__ import annotations

import time

from app.models.agent_state import CaseAnalysisOutput, ClaimWorkflowState, RetrievalQuery
from app.models.decision import TraceEvent


class CaseAnalysisAgent:
    name = "CaseAnalysisAgent"

    def run(self, state: ClaimWorkflowState) -> ClaimWorkflowState:
        started = time.perf_counter()
        case = state.case
        dimensions = ["coverage", "expense_limits", "required_evidence", "hospital_eligibility"]
        queries = [
            RetrievalQuery(dimension="coverage", query=f"hospitalization covered expenses {case.treatment.type} {case.treatment.procedure}"),
            RetrievalQuery(dimension="expense_limits", query="normal room boarding nursing per day Basic Sum Insured limit"),
            RetrievalQuery(dimension="expense_limits", query="medical practitioner anesthetist consultant surgeon fees Sum Insured limit"),
            RetrievalQuery(dimension="expense_limits", query="anesthesia operation theatre medicines drugs diagnostics x-ray Sum Insured limit"),
            RetrievalQuery(dimension="expense_limits", query="ambulance charges admissible claim Basic Sum Insured rupees limit"),
            RetrievalQuery(dimension="required_evidence", query="claims procedure bills receipts certificates information evidence medical practitioner hospital"),
            RetrievalQuery(dimension="hospital_eligibility", query="Hospital definition registered minimum criteria beds nursing medical practitioner operation theatre records"),
        ]
        if (case.claim_date - case.policy_start_date).days < 30 or case.prior_insurer_continuous_years:
            dimensions.append("initial_waiting_period")
            queries.append(RetrievalQuery(dimension="initial_waiting_period", query="30 days waiting period continuous previous insurer one year"))
        listed_first_year = ("cataract", "hernia", "hydrocele", "fistula", "piles", "arthritis", "gout", "rheumatism", "sinusitis", "stone", "tonsil", "ulcer")
        if case.continuous_coverage_months < 12 and any(term in f"{case.treatment.diagnosis} {case.treatment.procedure}".lower() for term in listed_first_year):
            dimensions.append("disease_specific_waiting")
            queries.append(RetrievalQuery(dimension="disease_specific_waiting", query=f"first year waiting period {case.treatment.diagnosis} {case.treatment.procedure} prior continuous one year"))
        if case.treatment.pre_existing:
            dimensions.append("pre_existing")
            queries.append(RetrievalQuery(dimension="pre_existing", query="pre-existing diseases 48 months continuous coverage portability reduced waiting period"))
        if case.treatment.type.lower() == "domiciliary":
            dimensions.append("domiciliary")
            queries.append(RetrievalQuery(dimension="domiciliary", query="domiciliary treatment home hospital room unavailable cannot be moved three days 20% sub-limit"))
        if case.treatment.type.lower() == "day_care" or case.treatment.admission_hours < 24:
            dimensions.append("day_care")
            queries.append(RetrievalQuery(dimension="day_care", query=f"day care treatment less than 24 hours technological advancement {case.treatment.procedure} {case.treatment.diagnosis}"))
        if case.treatment.experimental:
            dimensions.append("experimental_exclusion")
            queries.append(RetrievalQuery(dimension="experimental_exclusion", query="unproven experimental treatment not approved excluded"))
        if "cosmetic" in f"{case.treatment.diagnosis} {case.treatment.procedure}".lower():
            dimensions.append("cosmetic_exclusion")
            queries.append(RetrievalQuery(dimension="cosmetic_exclusion", query="cosmetic aesthetic treatment exclusion plastic surgery"))
        if case.expense_timing or case.expenses_inr.pre_hospitalization or case.expenses_inr.post_hospitalization:
            dimensions.append("expense_windows")
            queries.append(RetrievalQuery(dimension="expense_windows", query="pre-hospitalisation 30 days post hospitalisation 60 days same condition admissible"))
        missing = []
        context = case.evidence_context or {}
        if context.get("hospital_registered") is None and context.get("hospital_minimum_criteria_documented") is False:
            missing.append("Evidence that the facility is registered or meets the policy's minimum Hospital criteria")
        if "medical_necessity_confirmed" in context and context.get("medical_necessity_confirmed") is None:
            missing.append("Medical-practitioner evidence confirming medical necessity")
        if case.treatment.type.lower() == "domiciliary" and getattr(case.treatment, "treatment_days", None) is None:
            missing.append("Duration of domiciliary treatment to test the policy's three-day exclusion")
        state.analysis = CaseAnalysisOutput(
            facts=case.model_dump(mode="json"), relevant_dimensions=list(dict.fromkeys(dimensions)), missing_fields=missing,
            retrieval_queries=queries, investigation_checklist=[f"Resolve {d.replace('_', ' ')}" for d in dict.fromkeys(dimensions)],
        )
        state.trace.append(TraceEvent(agent=self.name, action="normalize_case_and_plan", elapsed_ms=(time.perf_counter()-started)*1000,
            brief_outcome=f"Created {len(queries)} focused retrieval queries"))
        return state
