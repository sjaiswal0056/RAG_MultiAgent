from functools import lru_cache

from app.graph.workflow import ClaimWorkflow
from app.services.policy_service import get_retriever


@lru_cache(maxsize=1)
def get_workflow() -> ClaimWorkflow:
    return ClaimWorkflow(get_retriever())
