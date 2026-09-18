from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    policy_path: Path = Path(os.getenv("POLICY_PATH", ROOT / "policy" / "USGIC-CSCIndividualHealthInsurance_2017-2018.pdf"))
    index_dir: Path = Path(os.getenv("INDEX_DIR", ROOT / "artifacts" / "index"))
    dense_top_k: int = int(os.getenv("DENSE_TOP_K", "10"))
    sparse_top_k: int = int(os.getenv("SPARSE_TOP_K", "10"))
    fused_top_k: int = int(os.getenv("FUSED_TOP_K", "12"))
    rerank_top_k: int = int(os.getenv("RERANK_TOP_K", "10"))
    rrf_k: int = int(os.getenv("RRF_K", "60"))
    max_validation_retries: int = int(os.getenv("MAX_VALIDATION_RETRIES", "1"))
    embedding_backend: str = os.getenv("EMBEDDING_BACKEND", "lsa")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    reranker_backend: str = os.getenv("RERANKER_BACKEND", "cross_feature")
    reranker_model: str = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
