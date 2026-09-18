from app.models.claim import ClaimCase


def test_all_public_cases_run(workflow, public_cases):
    results = [workflow.analyze(ClaimCase.model_validate(raw)) for raw in public_cases]
    assert len(results) == 12
    assert all(result.citations and result.validation.status == "PASS" for result in results)
