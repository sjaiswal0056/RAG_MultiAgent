import json
from pathlib import Path

import pytest

from app.graph.workflow import ClaimWorkflow
from app.ingestion.index_builder import build_index, load_chunks
from app.retrieval.hybrid_retriever import HybridRetriever


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def chunks():
    build_index()
    return load_chunks()


@pytest.fixture(scope="session")
def workflow(chunks):
    return ClaimWorkflow(HybridRetriever(chunks))


@pytest.fixture(scope="session")
def public_cases():
    return json.loads((ROOT / "candidate_data" / "public_test_cases.json").read_text(encoding="utf-8"))
