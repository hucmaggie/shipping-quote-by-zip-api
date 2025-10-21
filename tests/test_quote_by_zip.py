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
    # Basic shape checks
    for key in ["origin_zip","dest_zip","distance_km","total_usd"]:
        assert key in data
    assert data["dest_zip"] == "30301"
    assert data["origin_zip"] == "90001"

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