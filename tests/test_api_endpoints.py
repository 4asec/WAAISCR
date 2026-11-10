import pytest
from starlette.testclient import TestClient
from renderers.web_dashboard.app import app

def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "whatsapp" in data
    assert "app" in data
    assert data["app"]["name"] == "Link Curator"

def test_dashboard_page():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Link Curator Dashboard" in response.text

def test_webhook_unauthorized_ignored():
    client = TestClient(app)
    # Sender not in whitelist
    payload = {
        "sender": "111222333@s.whatsapp.net",
        "jid": "111222333@s.whatsapp.net",
        "is_group": False,
        "text": "/bantuan"
    }
    response = client.post("/api/webhook/whatsapp", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "received"}
