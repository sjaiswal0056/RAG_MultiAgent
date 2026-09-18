from __future__ import annotations


def reciprocal_rank_fusion(dense: list[dict], sparse: list[dict], k: int = 60, top_k: int = 12) -> list[dict]:
    merged: dict[str, dict] = {}
    for result_type, results in (("dense", dense), ("sparse", sparse)):
        for item in results:
            chunk_id = item["chunk"].chunk_id
            entry = merged.setdefault(chunk_id, {"chunk": item["chunk"], "fusion_score": 0.0})
            rank = item[f"{result_type}_rank"]
            entry["fusion_score"] += 1.0 / (k + rank)
            entry.update({key: value for key, value in item.items() if key != "chunk"})
    ordered = sorted(merged.values(), key=lambda item: (-item["fusion_score"], item["chunk"].chunk_id))
    return ordered[:top_k]
