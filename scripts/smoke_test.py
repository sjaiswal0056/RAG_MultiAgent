import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.graph.workflow import ClaimWorkflow
from app.ingestion.index_builder import load_chunks
from app.models.claim import ClaimCase
from app.retrieval.hybrid_retriever import HybridRetriever

root = Path(__file__).resolve().parents[1]
case = ClaimCase.model_validate(json.loads((root / "candidate_data" / "public_test_cases.json").read_text())[0])
print(ClaimWorkflow(HybridRetriever(load_chunks())).analyze(case).model_dump_json(indent=2))
