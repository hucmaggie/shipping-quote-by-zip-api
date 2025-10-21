from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Tuple
import math

app = FastAPI(title="Northstar Logistics - Shipping Cost by ZIP")

# ---------------- Knowledge Article 1 anchors ----------------
# Fees depend on:
# 1) package weight & dimensions (oversize/overweight may add handling),
# 2) delivery distance & mode (ground/air/express have different rate structures),
# 3) monthly fuel & regional surcharges.
#
# Example used for sanity checks in test data:
# "A 20 kg express shipment from Los Angeles to Atlanta ~ $55 incl. surcharges."
# (Adjust tunables to match this ballpark if desired.)

# ---------------- Simple ZIP -> (lat, lon) map ----------------
# NOTE: For production, replace this with a proper geocoding/centroid service or DB.
ZIP_DB: Dict[str, Tuple[float, float]] = {
    # LA (default origin DC), ATL, plus a few other common test ZIPs
    "90001": (33.973951, -118.248405),  # Los Angeles, CA
    "30301": (33.752880,  -84.392708),  # Atlanta, GA
    "10001": (40.750742,  -73.99653),   # New York, NY
    "60601": (41.886258,  -87.618844),  # Chicago, IL
    "73301": (30.267153,  -97.743057),  # Austin, TX
    "94105": (37.7898,   -122.3942),    # San Francisco, CA
}

def haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    (lat1, lon1), (lat2, lon2) = a, b
    R = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    h = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlmb/2)**2
    return 2*R*math.asin(math.sqrt(h))

# ---------------- Pricing tunables (transparent & tweakable) ----------------
DIM_DIVISOR_CM3_PER_KG = 5000.0  # common DIM factor
MODE_RATE_PER_KG = {"ground": 0.80, "air": 1.60, "express": 2.00}

def distance_multiplier(distance_km: float) -> float:
    # +5% per 1,000 km
    return 1.0 + 0.05 * (distance_km / 1000.0)

def handling_fee(weight_kg: float, length_cm: float, width_cm: float, height_cm: float) -> float:
    oversize = any(x > 100 for x in [length_cm, width_cm, height_cm]) or (length_cm + 2*(width_cm + height_cm)) > 300
    overweight = weight_kg > 30
    fee = 0.0
    if oversize:  fee += 10.0
    if overweight: fee += 15.0
    return fee

def round2(x: float) -> float:
    return round(float(x) + 1e-9, 2)

# ---------------- Request/Response models ----------------
class ZipQuoteRequest(BaseModel):
    # Only the destination ZIP is required; origin defaults to Northstar LA DC (90001)
    dest_zip: str = Field(description="Destination ZIP code")
    origin_zip: Optional[str] = Field(default="90001", description="Origin ZIP (defaults to Northstar LA DC)")
    weight_kg: float = Field(gt=0)
    length_cm: float = Field(gt=0)
    width_cm: float = Field(gt=0)
    height_cm: float = Field(gt=0)
    mode: Literal["ground", "air", "express"] = "ground"
    fuel_surcharge_pct: float = Field(default=12.0, ge=0)
    regional_surcharge_pct: float = Field(default=3.0, ge=0)
    enterprise_rate_card: bool = Field(default=False)

class ZipQuoteResponse(BaseModel):
    origin_zip: str
    dest_zip: str
    distance_km: float
    chargeable_weight_kg: float
    base_cost_usd: float
    distance_multiplier: float
    handling_fee_usd: float
    fuel_surcharge_usd: float
    regional_surcharge_usd: float
    enterprise_discount_usd: float
    total_usd: float
    notes: str

# ---------------- Core cost calculation (re-uses KA1 logic) ----------------
def compute_cost_from_distance_km(distance_km: float, *, weight_kg: float, length_cm: float, width_cm: float, height_cm: float,
                                  mode: str, fuel_pct: float, regional_pct: float, enterprise: bool) -> ZipQuoteResponse:
    dim_weight = (length_cm * width_cm * height_cm) / DIM_DIVISOR_CM3_PER_KG
    chargeable = max(weight_kg, dim_weight)
    rate = MODE_RATE_PER_KG[mode]
    base = chargeable * rate
    dmult = distance_multiplier(distance_km)
    base_adj = base * dmult
    h_fee = handling_fee(weight_kg, length_cm, width_cm, height_cm)
    fuel_fee = (fuel_pct / 100.0) * (base_adj + h_fee)
    regional_fee = (regional_pct / 100.0) * (base_adj + h_fee + fuel_fee)
    enterprise_discount = 0.10 * (base_adj + h_fee + fuel_fee + regional_fee) if enterprise else 0.0
    total = base_adj + h_fee + fuel_fee + regional_fee - enterprise_discount
    return ZipQuoteResponse(
        origin_zip="",
        dest_zip="",
        distance_km=round2(distance_km),
        chargeable_weight_kg=round2(chargeable),
        base_cost_usd=round2(base),
        distance_multiplier=round2(dmult),
        handling_fee_usd=round2(h_fee),
        fuel_surcharge_usd=round2(fuel_fee),
        regional_surcharge_usd=round2(regional_fee),
        enterprise_discount_usd=round2(enterprise_discount),
        total_usd=round2(total),
        notes=("Calculated per KA1: weight/dimensions, distance & mode, and fuel/regional surcharges. "
               "Enterprise discounts simulate pre-negotiated rate cards.")
    )

# ---------------- REST endpoint ----------------
@app.post("/quote-by-zip", response_model=ZipQuoteResponse)
def quote_by_zip(req: ZipQuoteRequest):
    if req.origin_zip not in ZIP_DB:
        raise HTTPException(status_code=400, detail=f"Unknown origin ZIP {req.origin_zip}. Add it to ZIP_DB or integrate a ZIP service.")
    if req.dest_zip not in ZIP_DB:
        raise HTTPException(status_code=400, detail=f"Unknown destination ZIP {req.dest_zip}. Add it to ZIP_DB or integrate a ZIP service.")

    origin_ll = ZIP_DB[req.origin_zip]
    dest_ll = ZIP_DB[req.dest_zip]
    distance_km = haversine_km(origin_ll, dest_ll)

    resp = compute_cost_from_distance_km(
        distance_km,
        weight_kg=req.weight_kg,
        length_cm=req.length_cm,
        width_cm=req.width_cm,
        height_cm=req.height_cm,
        mode=req.mode,
        fuel_pct=req.fuel_surcharge_pct,
        regional_pct=req.regional_surcharge_pct,
        enterprise=req.enterprise_rate_card,
    )
    resp.origin_zip = req.origin_zip
    resp.dest_zip = req.dest_zip
    return resp

# ---------------- Health check ----------------
@app.get('/health')
def health():
    return {'status': 'ok'}
