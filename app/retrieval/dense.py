from __future__ import annotations

import re
from collections import Counter

import numpy as np

from app.models.evidence import PolicyChunk


SYNONYMS = {
    "home": "domiciliary", "house": "domiciliary", "clinic": "hospital", "facility": "hospital",
    "before": "pre", "after": "post", "cap": "limit", "maximum": "limit", "unproven": "experimental",
    "aesthetic": "cosmetic", "preexisting": "pre existing", "portable": "portability", "continuous": "continuity",
}


def _terms(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9%]+", text.lower())
    normalized = [SYNONYMS.get(word, word) for word in words]
    terms: list[str] = []
    for word in normalized:
        terms.extend(word.split())
    terms.extend(f"{terms[i]}_{terms[i+1]}" for i in range(len(terms) - 1))
    return terms


class LSADenseRetriever:
    """Deterministic latent semantic analysis over the policy corpus."""

    def __init__(self, chunks: list[PolicyChunk], dimensions: int = 96):
        self.chunks = chunks
        documents = [_terms(f"{c.section} {c.heading} {c.text}") for c in chunks]
        df = Counter(term for doc in documents for term in set(doc))
        self.vocabulary = {term: index for index, term in enumerate(sorted(df))}
        n = len(documents)
        self.idf = np.array([np.log((1 + n) / (1 + df[term])) + 1 for term in sorted(df)], dtype=np.float32)
        matrix = np.zeros((n, len(self.vocabulary)), dtype=np.float32)
        for row, doc in enumerate(documents):
            counts = Counter(doc)
            for term, count in counts.items():
                matrix[row, self.vocabulary[term]] = (1 + np.log(count)) * self.idf[self.vocabulary[term]]
        rank = min(dimensions, max(1, min(matrix.shape) - 1))
        u, singular, vt = np.linalg.svd(matrix, full_matrices=False)
        self.components = vt[:rank].T
        self.matrix = u[:, :rank] * singular[:rank]
        norms = np.linalg.norm(self.matrix, axis=1, keepdims=True)
        self.matrix = np.divide(self.matrix, norms, out=np.zeros_like(self.matrix), where=norms != 0)

    def embed(self, text: str) -> np.ndarray:
        vector = np.zeros(len(self.vocabulary), dtype=np.float32)
        counts = Counter(_terms(text))
        for term, count in counts.items():
            index = self.vocabulary.get(term)
            if index is not None:
                vector[index] = (1 + np.log(count)) * self.idf[index]
        latent = vector @ self.components
        norm = float(np.linalg.norm(latent))
        return latent / norm if norm else latent

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        q = self.embed(query)
        scores = self.matrix @ q
        order = np.argsort(-scores)[:top_k]
        return [
            {"chunk": self.chunks[int(index)], "dense_score": float(scores[index]), "dense_rank": rank}
            for rank, index in enumerate(order, start=1)
            if scores[index] > 0
        ]


class SentenceTransformerDenseRetriever:
    def __init__(self, chunks: list[PolicyChunk], model_name: str):
        from sentence_transformers import SentenceTransformer

        self.chunks = chunks
        self.model = SentenceTransformer(model_name, local_files_only=True)
        texts = [f"{c.section} {c.heading} {c.text}" for c in chunks]
        self.matrix = self.model.encode(texts, normalize_embeddings=True)

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        q = self.model.encode([query], normalize_embeddings=True)[0]
        scores = self.matrix @ q
        order = np.argsort(-scores)[:top_k]
        return [
            {"chunk": self.chunks[int(index)], "dense_score": float(scores[index]), "dense_rank": rank}
            for rank, index in enumerate(order, start=1)
        ]


# Backward-compatible name used by tests and callers from the first implementation.
HashingDenseRetriever = LSADenseRetriever
