<<<<<<< HEAD
# shipping-quote-by-zip-api
=======
# Northstar Shipping Cost API (ZIP-based)

FastAPI service that calculates shipping costs using Knowledge Article 1 rules and distance derived from US ZIP codes.
- Pillars: weight & dimensions, distance & mode, fuel/regional surcharges
- Endpoint: `POST /quote-by-zip`

## 1) Open in Cursor
- **File → Open Folder…** and select this project folder.
- If prompted, let Cursor create a virtual environment.

## 2) Create & activate a venv (recommended)
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

## 3) Install dependencies
```bash
pip install -r requirements.txt
```

## 4) Run the API (hot reload)
```bash
uvicorn app:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json

## 5) Try it (requests.http)
If you use the REST Client extension, open `requests.http` and click **Send Request** above a request.

Or with curl:
```bash
curl -s http://localhost:8000/quote-by-zip -H "Content-Type: application/json" -d '{
  "dest_zip": "30301",
  "weight_kg": 20,
  "length_cm": 40,
  "width_cm": 30,
  "height_cm": 30,
  "mode": "express"
}'
```

## 6) Common Cursor tips
- Use **Run/Debug** to launch `uvicorn` with breakpoints.
- Press **⌘⇧P** (macOS) / **Ctrl+Shift+P** (Windows) → *Python: Select Interpreter* → choose `.venv`.
- Use **Chat (CMD+L)** in Cursor to refactor functions or add tests.

## 7) Customize
- Replace the in-file `ZIP_DB` with your internal ZIP centroid DB or API.
- Plug enterprise discounts into your real rate-card service.
- Adjust DIM divisor and per-mode rates to match KA1 precisely.

## 8) Production notes
- Add logging, request IDs, and validation guards.
- Containerize with a `Dockerfile` and run behind a reverse proxy (e.g., Nginx, API Gateway).
- CI/CD: include unit tests and contract tests for pricing logic.

---
## 9) Run tests
```bash
pytest -q
```


---
## 10) Deploy to Render (one-click)
1. Push this folder to GitHub.
2. In Render: New → Web Service → "Build & deploy from a Git repository".
3. Select the repo; Render will detect `render.yaml`.
4. First deploy gives you an HTTPS URL (e.g., https://northstar-shipping-zip-api.onrender.com).
   - Swagger UI: /docs
   - Health: /health


---
## 11) GitHub Actions: test & auto-deploy to Render
This repo includes `.github/workflows/render-deploy.yml` which:
1. Installs deps
2. Runs `pytest`
3. If tests pass, triggers a Render deploy via a **Deploy Hook URL**

**Setup once:**
- In Render, open your service → **Settings** → **Deploy Hooks** → create a hook for the `main` branch.
- Copy the URL and add it to your GitHub repo as an Actions secret named **RENDER_DEPLOY_HOOK_URL**.
  - GitHub → *Settings* → *Secrets and variables* → *Actions* → *New repository secret*.

On every push to `main`, tests run and (if green) a deploy is triggered automatically.
>>>>>>> bb03542 (Initial commit: Northstar Shipping ZIP API)
