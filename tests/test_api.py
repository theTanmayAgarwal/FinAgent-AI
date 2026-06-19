from fastapi.testclient import TestClient

from finagent.api.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_auth_and_research_flow(monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setattr(
        "finagent.api.routes.research.get_settings",
        lambda: SimpleNamespace(market_data_mode="demo"),
    )
    with TestClient(app) as client:
        email = "test-flow@example.com"
        signup = client.post(
            "/api/v1/auth/signup", json={"email": email, "password": "a-very-safe-password"}
        )
        if signup.status_code == 409:
            signup = client.post(
                "/api/v1/auth/token", data={"username": email, "password": "a-very-safe-password"}
            )
        token = signup.json()["access_token"]
        response = client.post(
            "/api/v1/research",
            json={"ticker": "DEMO"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    assert len(response.json()["evidence"]) == 12
