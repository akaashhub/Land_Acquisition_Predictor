"""
SIH26017 — Predictive Analytics System for Early Detection of Land Acquisition Delays
FastAPI application entry point.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.database import init_db, SessionLocal, engine
from app.database.models import User, Project, Prediction, ModelMetrics
from app.api import auth, projects, analytics, alerts, upload, what_if, model_api
from app.api.auth import hash_password, DEMO_USERS
from app.ml.generate_dataset import generate_dataset, generate_demo_projects
from app.services.prediction_service import run_full_prediction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sih26017")
settings = get_settings()


def seed_users(db: Session):
    for username, info in DEMO_USERS.items():
        existing = db.query(User).filter(User.username == username).first()
        if not existing:
            db.add(User(
                username=username,
                hashed_password=hash_password(info["password"]),
                role=info["role"],
                full_name=info["full_name"],
            ))
    db.commit()


def seed_projects(db: Session, max_projects: int = 500):
    """Load synthetic + demo projects and run predictions."""
    count = db.query(Project).count()
    if count > 0:
        logger.info(f"Projects already seeded ({count})")
        return

    logger.info("Generating synthetic demonstration dataset...")
    df = generate_dataset(max_projects)
    # Prefer demo projects first
    demos = generate_demo_projects()
    demo_ids = {d["project_id"] for d in demos}

    records = demos + [r for r in df.to_dict(orient="records") if r["project_id"] not in demo_ids]
    records = records[:max_projects]

    logger.info(f"Seeding {len(records)} projects...")
    for i, row in enumerate(records):
        # Clean None delay_stage
        if row.get("delay_stage") is None:
            row["delay_stage"] = None
        # Only keep model columns
        cols = {c.name for c in Project.__table__.columns}
        data = {k: v for k, v in row.items() if k in cols}
        p = Project(**data)
        db.add(p)
        if (i + 1) % 100 == 0:
            db.flush()
            logger.info(f"  inserted {i + 1}/{len(records)}")
    db.commit()

    # Run predictions in batches
    logger.info("Running ML predictions on all projects...")
    projects = db.query(Project).all()
    for i, p in enumerate(projects):
        try:
            run_full_prediction(db, p, create_alert=(p.is_demo or p.project_id.startswith("LA-1")))
        except Exception as e:
            logger.warning(f"Prediction failed for {p.project_id}: {e}")
        if (i + 1) % 50 == 0:
            logger.info(f"  predicted {i + 1}/{len(projects)}")
    db.commit()
    logger.info("Seeding complete.")


def ensure_models():
    models_dir = Path(__file__).parent / "ml" / "models"
    clf = models_dir / "delay_classifier.joblib"
    if not clf.exists():
        logger.info("Training ML models (first run)...")
        from app.ml.train import train_all
        train_all(n_samples=2500)
    else:
        logger.info("ML models found.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    ensure_models()
    db = SessionLocal()
    try:
        seed_users(db)
        seed_projects(db, max_projects=400)
    finally:
        db.close()
    yield


app = FastAPI(
    title="SIH26017 — Land Acquisition Delay Prediction",
    description=(
        "Predictive Analytics System for Early Detection of Land Acquisition Delays. "
        "Demonstration Dataset — Synthetic Data. "
        "Predictions are estimates that support, not replace, administrative judgment."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(what_if.router)
app.include_router(analytics.router)
app.include_router(alerts.router)
app.include_router(upload.router)
app.include_router(model_api.router)


@app.get("/")
def root():
    return {
        "system": "SIH26017",
        "title": "Predictive Analytics System for Early Detection of Land Acquisition Delays",
        "loop": "DATA → PREDICT → EXPLAIN → RECOMMEND → SIMULATE → MONITOR",
        "disclaimer": (
            "Demonstration Dataset — Synthetic Data. "
            "Predictions are model-based estimates and not guaranteed outcomes."
        ),
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "database": "connected"}


@app.get("/api/upload/sample-csv/download")
def download_sample():
    path = Path(__file__).resolve().parents[1] / "data" / "sample_dataset.csv"
    if not path.exists():
        from app.ml.generate_dataset import generate_dataset
        path.parent.mkdir(parents=True, exist_ok=True)
        generate_dataset(100).to_csv(path, index=False)
    return FileResponse(path, filename="sample_land_acquisition.csv", media_type="text/csv")
