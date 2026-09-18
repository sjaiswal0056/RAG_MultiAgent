from __future__ import annotations


def safe_div(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def summarize(records: list[dict]) -> dict:
    total = len(records)
    correct = sum(item["decision_correct"] for item in records)
    evidence_hits = sum(item["evidence_hit"] for item in records)
    expected_abstentions = sum(item["expected_decision"] == "NEEDS_REVIEW" for item in records)
    correct_abstentions = sum(item["expected_decision"] == item["actual_decision"] == "NEEDS_REVIEW" for item in records)
    unsafe_answers = sum(item["expected_decision"] == "NEEDS_REVIEW" and item["actual_decision"] != "NEEDS_REVIEW" for item in records)
    unnecessary_abstentions = sum(item["expected_decision"] != "NEEDS_REVIEW" and item["actual_decision"] == "NEEDS_REVIEW" for item in records)
    material = sum(item["material_claim_count"] for item in records)
    supported = sum(item["supported_material_claim_count"] for item in records)
    valid = sum(item["valid_citation_count"] for item in records)
    invalid = sum(item["invalid_citation_count"] for item in records)
    return {
        "case_count": total,
        "decision_accuracy": safe_div(correct, total),
        "evidence_recall_at_k": safe_div(evidence_hits, total),
        "material_claim_count": material,
        "supported_material_claim_count": supported,
        "citation_coverage_rate": safe_div(supported, material),
        "valid_citation_count": valid,
        "invalid_citation_count": invalid,
        "citation_support_rate": safe_div(valid, valid + invalid),
        "expected_abstentions": expected_abstentions,
        "correct_abstentions": correct_abstentions,
        "unsafe_answers_when_should_abstain": unsafe_answers,
        "unnecessary_abstentions": unnecessary_abstentions,
    }
