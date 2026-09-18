from app.agents.case_analysis import CaseAnalysisAgent
from app.models.agent_state import ClaimWorkflowState
from app.models.claim import ClaimCase


def test_agents_exchange_structured_state(public_cases):
    state = ClaimWorkflowState(case=ClaimCase.model_validate(public_cases[4]))
    result = CaseAnalysisAgent().run(state)
    assert result.analysis is not None
    assert result.analysis.retrieval_queries
    assert all(query.dimension and query.query for query in result.analysis.retrieval_queries)
