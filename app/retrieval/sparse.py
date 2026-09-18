from __future__ import annotations

import math
import re
from collections import Counter

from app.models.evidence import PolicyChunk


TOKEN_RE = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?%?", re.I)


def tokenize(text: str) -> list[str]:
    tokens = TOKEN_RE.findall(text.lower())
    return [token[:-1] if len(token) > 4 and token.endswith("s") and not token.endswith("ss") else token for token in tokens]


class BM25Retriever:
    def __init__(self, chunks: list[PolicyChunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1, self.b = k1, b
        self.docs = [tokenize(f"{c.section} {c.heading} {c.text}") for c in chunks]
        self.lengths = [len(doc) for doc in self.docs]
        self.avgdl = sum(self.lengths) / max(len(self.lengths), 1)
        self.tfs = [Counter(doc) for doc in self.docs]
        df: Counter[str] = Counter()
        for doc in self.docs:
            df.update(set(doc))
        n = len(self.docs)
        self.idf = {term: math.log(1 + (n - freq + 0.5) / (freq + 0.5)) for term, freq in df.items()}

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        q = tokenize(query)
        scored = []
        for index, tf in enumerate(self.tfs):
            score = 0.0
            for term in q:
                freq = tf.get(term, 0)
                if not freq:
                    continue
                denominator = freq + self.k1 * (1 - self.b + self.b * self.lengths[index] / max(self.avgdl, 1))
                score += self.idf.get(term, 0) * (freq * (self.k1 + 1) / denominator)
            if score > 0:
                scored.append((score, index))
        scored.sort(reverse=True)
        return [
            {"chunk": self.chunks[index], "sparse_score": score, "sparse_rank": rank}
            for rank, (score, index) in enumerate(scored[:top_k], start=1)
        ]
