from __future__ import annotations

import json
from pathlib import Path

from app.graph.workflow import ClaimWorkflow
from app.ingestion.index_builder import build_index, load_chunks
from app.models.claim import ClaimCase
from app.retrieval.hybrid_retriever import HybridRetriever
from evaluation.metrics import summarize


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_group(cases: list[dict], expected: dict, workflow: ClaimWorkflow) -> tuple[list[dict], list[dict]]:
    summaries, full_results = [], []
    for raw in cases:
        case = ClaimCase.model_validate(raw)
        decision = workflow.analyze(case)
        exp = expected[case.case_id]
        text = " ".join(c.excerpt.lower() for c in decision.citations)
        evidence_hit = all(any(term.lower() in text for term in alternatives) for alternatives in exp["evidence_terms"])
        invalid = len(decision.validation.invalid_citations)
        material = sum(f.status != "UNCERTAIN" for f in decision.key_findings)
        cited = len({citation.claim for citation in decision.citations})
        summaries.append({
            "case_id": case.case_id, "expected_decision": exp["decision"], "actual_decision": decision.decision,
            "decision_correct": decision.decision == exp["decision"], "evidence_hit": evidence_hit,
            "material_claim_count": material, "supported_material_claim_count": min(material, cited),
            "valid_citation_count": len(decision.citations) - invalid, "invalid_citation_count": invalid,
        })
        full_results.append(decision.model_dump(mode="json"))
    return summaries, full_results


def main() -> None:
    manifest = build_index()
    workflow = ClaimWorkflow(HybridRetriever(load_chunks()))
    expected = load_json(ROOT / "evaluation" / "expected_outcomes.json")
    public_cases = load_json(ROOT / "candidate_data" / "public_test_cases.json")
    candidate_cases = load_json(ROOT / "evaluation" / "candidate_test_cases.json")
    public_summary, public_results = evaluate_group(public_cases, expected, workflow)
    candidate_summary, candidate_results = evaluate_group(candidate_cases, expected, workflow)
    metrics = {
        "index": manifest,
        "public": summarize(public_summary),
        "candidate": summarize(candidate_summary),
        "combined": summarize(public_summary + candidate_summary),
        "case_results": public_summary + candidate_summary,
    }
    result_dir = ROOT / "evaluation" / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    (result_dir / "public_results.json").write_text(json.dumps(public_results, indent=2), encoding="utf-8")
    (result_dir / "candidate_results.json").write_text(json.dumps(candidate_results, indent=2), encoding="utf-8")
    (result_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
