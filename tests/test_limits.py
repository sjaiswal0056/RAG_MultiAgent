from app.models.claim import ClaimCase
from app.services.limit_calculator import calculate_limits


def test_limit_arithmetic_is_deterministic(public_cases):
    case = ClaimCase.model_validate(public_cases[0])
    one = calculate_limits(case)
    two = calculate_limits(case)
    assert one == two
    assert one[2] == 153000.0
    assert any(item["category"] == "ambulance" and item["deduction_inr"] == 200 for item in one[1])
