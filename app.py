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
    # Only the destination ZIP is required; all other fields have sensible defaults
    dest_zip: str = Field(description="Destination ZIP code")
    origin_zip: Optional[str] = Field(default="90001", description="Origin ZIP (defaults to Northstar LA DC)")
    weight_kg: Optional[float] = Field(default=1.0, gt=0, description="Package weight in kg (default: 1.0 kg)")
    length_cm: Optional[float] = Field(default=30.0, gt=0, description="Package length in cm (default: 30.0 cm)")
    width_cm: Optional[float] = Field(default=20.0, gt=0, description="Package width in cm (default: 20.0 cm)")
    height_cm: Optional[float] = Field(default=10.0, gt=0, description="Package height in cm (default: 10.0 cm)")
    mode: Optional[Literal["ground", "air", "express"]] = Field(default="ground", description="Shipping mode (default: ground)")
    fuel_surcharge_pct: Optional[float] = Field(default=12.0, ge=0, description="Fuel surcharge percentage (default: 12.0%)")
    regional_surcharge_pct: Optional[float] = Field(default=3.0, ge=0, description="Regional surcharge percentage (default: 3.0%)")
    enterprise_rate_card: Optional[bool] = Field(default=False, description="Apply enterprise discount (default: False)")

class ZipQuoteResponse(BaseModel):
    total_usd: float

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
        total_usd=round2(total)
    )

# ---------------- REST endpoint ----------------
@app.post("/quote-by-zip", response_model=ZipQuoteResponse)
def quote_by_zip(req: ZipQuoteRequest):
    # Use defaults for optional fields if not provided
    origin_zip = req.origin_zip or "90001"
    weight_kg = req.weight_kg or 1.0
    length_cm = req.length_cm or 30.0
    width_cm = req.width_cm or 20.0
    height_cm = req.height_cm or 10.0
    mode = req.mode or "ground"
    fuel_pct = req.fuel_surcharge_pct or 12.0
    regional_pct = req.regional_surcharge_pct or 3.0
    enterprise = req.enterprise_rate_card or False
    
    if origin_zip not in ZIP_DB:
        raise HTTPException(status_code=400, detail=f"Unknown origin ZIP {origin_zip}. Add it to ZIP_DB or integrate a ZIP service.")
    if req.dest_zip not in ZIP_DB:
        raise HTTPException(status_code=400, detail=f"Unknown destination ZIP {req.dest_zip}. Add it to ZIP_DB or integrate a ZIP service.")

    origin_ll = ZIP_DB[origin_zip]
    dest_ll = ZIP_DB[req.dest_zip]
    distance_km = haversine_km(origin_ll, dest_ll)

    resp = compute_cost_from_distance_km(
        distance_km,
        weight_kg=weight_kg,
        length_cm=length_cm,
        width_cm=width_cm,
        height_cm=height_cm,
        mode=mode,
        fuel_pct=fuel_pct,
        regional_pct=regional_pct,
        enterprise=enterprise,
    )
    return resp

# ---------------- Health check ----------------
@app.get('/health')
def health():
    return {'status': 'ok'}
