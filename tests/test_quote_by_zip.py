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
    # Check all expected fields are in the response
    expected_fields = [
        "base_cost_usd", "distance_multiplier", "handling_fee_usd", 
        "fuel_surcharge_usd", "regional_surcharge_usd", "enterprise_discount_usd", "total_usd"
    ]
    for field in expected_fields:
        assert field in data
    
    # Check USD fields are formatted as currency strings
    usd_fields = ["base_cost_usd", "handling_fee_usd", "fuel_surcharge_usd", 
                  "regional_surcharge_usd", "enterprise_discount_usd", "total_usd"]
    for field in usd_fields:
        assert isinstance(data[field], str)
        assert data[field].startswith("$")
        assert "," in data[field] or "." in data[field]  # Currency format
    
    # Check distance_multiplier is a number
    assert isinstance(data["distance_multiplier"], (int, float))

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