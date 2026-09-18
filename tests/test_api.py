from fastapi.testclient import TestClient

from app.api.main import app


def test_health_and_analyze(public_cases):
    with TestClient(app) as client:
        assert client.get("/health").json()["status"] == "ok"
        response = client.post("/analyze", json=public_cases[0])
        assert response.status_code == 200
        assert response.json()["case_id"] == "PUB-001"


def test_invalid_input_is_4xx():
    with TestClient(app) as client:
        response = client.post("/analyze", json={"case_id": "broken"})
        assert response.status_code == 422
