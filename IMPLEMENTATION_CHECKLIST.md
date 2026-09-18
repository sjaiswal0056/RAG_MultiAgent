# Requirement Traceability

| Requirement | Code | Test | Documentation | Evaluation artifact |
|---|---|---|---|---|
| Page-aware section chunks | `app/ingestion` | `test_chunking.py` | README, Architecture | `artifacts/index/manifest.json` |
| Dense semantic retrieval | `retrieval/dense.py` | `test_dense_retrieval.py` | README, Architecture | results metrics |
| BM25 and RRF | `sparse.py`, `fusion.py` | sparse/hybrid tests | README, Architecture | results metrics |
| Separate reranking | `reranker.py` | `test_reranking.py` | README, Architecture | result traces |
| Five specialized agents | `app/agents` | `test_agents.py` | README, Architecture | public/candidate results |
| Structured state | `models/agent_state.py` | `test_agents.py` | Architecture | result traces |
| Citation validation/retry | `validation.py`, `workflow.py` | `test_validation.py` | README, Architecture | citation metrics |
| Safe abstention | decision/workflow agents | `test_abstention.py` | README | abstention metrics |
| Deterministic limits | `limit_calculator.py` | `test_limits.py` | README | case results |
| FastAPI | `app/api` | `test_api.py` | README | smoke test |
| Streamlit | `frontend/streamlit_app.py` | import/start check | README, Deployment | manual UI check |
| 12 public + 5 candidate cases | `evaluation` | `test_public_cases.py` | Evaluation report | JSON results/metrics |
| Reproducible deployment | Dockerfile, render config | container/import checks | Deployment | build/runtime logs |
