# Northstar Shipping Cost API (ZIP-based)

FastAPI service that calculates shipping costs using Knowledge Article 1 rules and distance derived from US ZIP codes.
- **Simplified API**: Only requires destination ZIP, returns total cost
- **Smart defaults**: Uses sensible defaults for package dimensions and shipping options
- **Endpoint**: `POST /quote-by-zip`

## Features

- ✅ **Minimal input**: Only destination ZIP required
- ✅ **Smart defaults**: 1kg package, ground shipping, standard dimensions
- ✅ **Flexible**: Override any parameter when needed
- ✅ **Simple response**: Returns only the total shipping cost
- ✅ **Production ready**: Deployed on Render with health checks

## Quick Start

### 1) Open in Cursor
- **File → Open Folder…** and select this project folder.
- If prompted, let Cursor create a virtual environment.

### 2) Create & activate a venv (recommended)
**macOS/Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3) Install dependencies
```bash
pip install -r requirements.txt
```

### 4) Run the API (hot reload)
```bash
uvicorn app:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

## API Usage

### Minimal Request (Recommended)
```bash
curl -X POST "http://localhost:8000/quote-by-zip" \
  -H "Content-Type: application/json" \
  -d '{"dest_zip": "30301"}'
```

**Response:**
```json
{"total_usd": 1.28}
```

### Custom Request (Optional)
```bash
curl -X POST "http://localhost:8000/quote-by-zip" \
  -H "Content-Type: application/json" \
  -d '{
    "dest_zip": "30301",
    "weight_kg": 5.0,
    "length_cm": 40,
    "width_cm": 30,
    "height_cm": 20,
    "mode": "express"
  }'
```

## Request Parameters

| Parameter | Required | Default | Description |
|-----------|----------|--------|-------------|
| `dest_zip` | ✅ Yes | - | Destination ZIP code |
| `origin_zip` | ❌ No | "90001" | Origin ZIP (defaults to LA) |
| `weight_kg` | ❌ No | 1.0 | Package weight in kg |
| `length_cm` | ❌ No | 30.0 | Package length in cm |
| `width_cm` | ❌ No | 20.0 | Package width in cm |
| `height_cm` | ❌ No | 10.0 | Package height in cm |
| `mode` | ❌ No | "ground" | Shipping mode: "ground", "air", "express" |
| `fuel_surcharge_pct` | ❌ No | 12.0 | Fuel surcharge percentage |
| `regional_surcharge_pct` | ❌ No | 3.0 | Regional surcharge percentage |
| `enterprise_rate_card` | ❌ No | false | Apply enterprise discount |

## Response Format

```json
{
  "total_usd": 1.28
}
```

## Supported ZIP Codes

Currently supports these test ZIP codes:
- `90001` - Los Angeles, CA (default origin)
- `30301` - Atlanta, GA
- `10001` - New York, NY
- `60601` - Chicago, IL
- `73301` - Austin, TX
- `94105` - San Francisco, CA

## Testing

### Run tests
```bash
pytest -q
```

### Test with requests.http
If you use the REST Client extension, open `requests.http` and click **Send Request** above a request.

## Deployment

### Deploy to Render (one-click)
1. Push this folder to GitHub
2. In Render: New → Web Service → "Build & deploy from a Git repository"
3. Select the repo; Render will detect `render.yaml`
4. First deploy gives you an HTTPS URL (e.g., https://northstar-shipping-zip-api.onrender.com)

### Test deployed API
```bash
# Health check
curl https://your-app-name.onrender.com/health

# Shipping quote
curl -X POST "https://your-app-name.onrender.com/quote-by-zip" \
  -H "Content-Type: application/json" \
  -d '{"dest_zip": "30301"}'
```

## Development Tips

### Common Cursor tips
- Use **Run/Debug** to launch `uvicorn` with breakpoints
- Press **⌘⇧P** (macOS) / **Ctrl+Shift+P** (Windows) → *Python: Select Interpreter* → choose `.venv`
- Use **Chat (CMD+L)** in Cursor to refactor functions or add tests

### Customization
- Replace the in-file `ZIP_DB` with your internal ZIP centroid DB or API
- Plug enterprise discounts into your real rate-card service
- Adjust DIM divisor and per-mode rates to match KA1 precisely

### Production notes
- Add logging, request IDs, and validation guards
- Containerize with a `Dockerfile` and run behind a reverse proxy (e.g., Nginx, API Gateway)
- CI/CD: include unit tests and contract tests for pricing logic

## GitHub Actions: test & auto-deploy to Render

This repo includes `.github/workflows/render-deploy.yml` which:
1. Installs deps
2. Runs `pytest`
3. If tests pass, triggers a Render deploy via a **Deploy Hook URL**

**Setup once:**
- In Render, open your service → **Settings** → **Deploy Hooks** → create a hook for the `main` branch
- Copy the URL and add it to your GitHub repo as an Actions secret named **RENDER_DEPLOY_HOOK_URL**
  - GitHub → *Settings* → *Secrets and variables* → *Actions* → *New repository secret*

On every push to `main`, tests run and (if green) a deploy is triggered automatically.