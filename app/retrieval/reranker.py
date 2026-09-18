from __future__ import annotations

import re

from app.retrieval.sparse import tokenize


class CrossFeatureReranker:
    """Offline second-stage reranker scoring each query-document pair jointly."""

    def score(self, query: str, text: str, heading: str) -> float:
        q = set(tokenize(query))
        body = set(tokenize(text))
        head = set(tokenize(heading))
        if not q:
            return 0.0
        coverage = len(q & body) / len(q)
        heading_overlap = len(q & head) / len(q)
        phrase_hits = sum(1 for phrase in re.findall(r"[a-z]+(?: [a-z]+){1,3}", query.lower()) if phrase in text.lower())
        q_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", query))
        number_hits = len(q_numbers & set(re.findall(r"\d+(?:\.\d+)?%?", text)))
        return coverage + 0.45 * heading_overlap + 0.15 * phrase_hits + 0.1 * number_hits

    def rerank(self, query: str, candidates: list[dict], top_k: int = 6) -> list[dict]:
        rescored = []
        for position, item in enumerate(candidates, start=1):
            clone = dict(item)
            chunk = item["chunk"]
            clone["pre_rerank_position"] = position
            clone["rerank_score"] = self.score(query, chunk.text, chunk.heading)
            rescored.append(clone)
        rescored.sort(key=lambda item: (-item["rerank_score"], -item["fusion_score"], item["chunk"].chunk_id))
        for rank, item in enumerate(rescored[:top_k], start=1):
            item["final_rank"] = rank
        return rescored[:top_k]
