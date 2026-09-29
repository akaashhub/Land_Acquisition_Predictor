# SIH26017 — Predictive Analytics System for Early Detection of Land Acquisition Delays

**Smart India Hackathon 2026 prototype**

Core loop: **DATA → PREDICT → EXPLAIN → RECOMMEND → SIMULATE → MONITOR**

> **Demonstration Dataset — Synthetic Data.** Predictions are model-based estimates that support, not replace, administrative judgment.

## Quick start

### 1. Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Optional: retrain (trained models are already included under app/ml/models/)
# PYTHONPATH=. python -m app.ml.train

export PYTHONPATH=.
# Linux/macOS:
export DATABASE_URL=sqlite:///./land_acquisition.db
# Windows PowerShell: $env:DATABASE_URL="sqlite:///./land_acquisition.db"

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
API docs: http://localhost:8000/docs  
On first start the app creates the SQLite DB and seeds projects + predictions.

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
App: http://localhost:5173

### Demo credentials
| User    | Password    | Role    |
|---------|-------------|---------|
| admin   | admin123    | ADMIN   |
| officer | officer123  | OFFICER |
| viewer  | viewer123   | VIEWER  |

### Sample project IDs
- **LA-1024** — Judge demo (Highway, Pune)
- **LA-1101** — Critical legal / court stay
- **LA-1050** — Low risk
- **LA-1088** — Compensation bottleneck
- **LA-1075** — Documentation bottleneck

## Package contents
- `backend/` — FastAPI, ML pipeline, trained `.joblib` models, sample CSV
- `frontend/` — React + TypeScript + Vite + Tailwind UI
- `README.md`, `docker-compose.yml`, `.gitignore`
- Config examples: `backend/.env.example`, `frontend/.env.example`

## Technology stack
- Frontend: React, TypeScript, Vite, Tailwind, Recharts, Leaflet
- Backend: Python, FastAPI, SQLAlchemy, scikit-learn, joblib
- DB: SQLite (local) / PostgreSQL via `DATABASE_URL`

## 5-minute judge demo
1. Login → Dashboard KPIs  
2. Risk Monitor → critical project  
3. Project detail: risk, probability, delay, stage  
4. WHY? risk factors  
5. WHAT SHOULD WE DO? recommendations  
6. Stage risk chart  
7. What-If simulator  
8. Update project (e.g. court stay) → risk change  
9. Early Warnings  
10. Map  

## Limitations
- Synthetic demonstration data only  
- Prototype risk thresholds (not official)  
- Retrain on real government data before production  

## License
Hackathon prototype — SIH 2026
