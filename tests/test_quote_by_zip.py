import json
from fastapi.testclient import TestClient
import importlib

app_module = importlib.import_module("app")
app = app_module.app
client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_quote_by_zip_minimal():
    payload = {
        "dest_zip": "30301",
        "weight_kg": 20,
        "length_cm": 40,
        "width_cm": 30,
        "height_cm": 30,
        "mode": "express"
    }
    r = client.post("/quote-by-zip", json=payload)
    assert r.status_code == 200
    data = r.json()
    # Only total_usd should be in the response
    assert "total_usd" in data
    assert len(data) == 1  # Only one field
    assert isinstance(data["total_usd"], (int, float))
    assert data["total_usd"] > 0

def test_quote_by_zip_unknown_zip():
    payload = {
        "dest_zip": "99999",
        "weight_kg": 1,
        "length_cm": 10,
        "width_cm": 10,
        "height_cm": 10,
    }
    r = client.post("/quote-by-zip", json=payload)
    assert r.status_code == 400