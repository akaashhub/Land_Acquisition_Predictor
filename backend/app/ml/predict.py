"""Prediction utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
import joblib

from app.ml.preprocessing import Preprocessor
from app.ml.feature_engineering import engineer_features

MODELS_DIR = Path(__file__).parent / "models"

_classifier = None
_regressor = None
_preprocessor = None
_meta = None


def load_models():
    global _classifier, _regressor, _preprocessor, _meta
    clf_path = MODELS_DIR / "delay_classifier.joblib"
    reg_path = MODELS_DIR / "delay_regressor.joblib"
    prep_path = MODELS_DIR / "preprocessor.joblib"
    meta_path = MODELS_DIR / "metrics.json"

    if not clf_path.exists():
        from app.ml.train import train_all
        train_all()

    _classifier = joblib.load(clf_path)
    _regressor = joblib.load(reg_path)
    _preprocessor = Preprocessor.load(prep_path)
    if meta_path.exists():
        import json
        with open(meta_path) as f:
            _meta = json.load(f)
    return _classifier, _regressor, _preprocessor


def get_models():
    global _classifier, _regressor, _preprocessor
    if _classifier is None:
        load_models()
    return _classifier, _regressor, _preprocessor


def risk_category(score: float) -> str:
    """Prototype risk classification thresholds (not official)."""
    if score <= 25:
        return "LOW"
    if score <= 50:
        return "MEDIUM"
    if score <= 75:
        return "HIGH"
    return "CRITICAL"


def project_to_df(project: dict | Any) -> pd.DataFrame:
    if hasattr(project, "__dict__") and not isinstance(project, dict):
        d = {c.name: getattr(project, c.name, None)
             for c in project.__table__.columns}
    else:
        d = dict(project)
    return pd.DataFrame([d])



def _heuristic_risk(row: dict) -> float:
    """Transparent risk score used to calibrate ML output for demonstration."""
    s = 18.0
    if row.get("court_stay"):
        s += 28
    if row.get("legal_dispute"):
        s += 10 + float(row.get("number_of_active_cases") or 0) * 3.5
    s += float(row.get("dispute_severity") or 0) * 4
    if row.get("ownership_conflict"):
        s += 8
    s += min(float(row.get("objection_count") or 0) * 1.5, 12)
    comp = float(row.get("compensation_completion_percentage") or 50)
    s += max(0, (75 - comp) * 0.32)
    doc = float(row.get("documentation_completion_percentage") or 50)
    s += max(0, (80 - doc) * 0.28)
    s += min(float(row.get("pending_approvals") or 0) * 3.2, 16)
    s += min(float(row.get("approval_delay_days") or 0) * 0.07, 8)
    s += max(0, (60 - float(row.get("stakeholder_response_rate") or 50)) * 0.22)
    s += min(float(row.get("unresolved_grievances") or 0) * 1.8, 10)
    s += max(0, float(row.get("progress_variance") or 0) * 0.35)
    s += float(row.get("district_historical_delay_rate") or 0.3) * 22
    if row.get("rehabilitation_required"):
        s += max(0, (60 - float(row.get("rehabilitation_completion_percentage") or 0)) * 0.2)
    import numpy as np
    return float(np.clip(s, 5, 100))

def predict_project(project: dict | Any) -> dict:
    clf, reg, prep = get_models()
    df = project_to_df(project)
    X = prep.transform(df)

    proba_raw = float(clf.predict_proba(X)[0][1])
    # Transparent heuristic score for better calibration/spread on demo data
    row = df.iloc[0].to_dict()
    heuristic = _heuristic_risk(row)
    # Blend: 55% model + 45% heuristic → better separation for demo
    proba = 0.35 * proba_raw + 0.65 * (heuristic / 100.0)
    proba = float(min(max(proba, 0.02), 0.98))
    risk_score = round(proba * 100, 1)
    category = risk_category(risk_score)
    est_delay = max(0.0, float(reg.predict(X)[0]))
    # Scale estimated delay toward heuristic as well
    est_delay = round(min(0.6 * est_delay + 0.4 * (heuristic * 1.1), 300), 1)

    bottleneck = _infer_bottleneck(df.iloc[0].to_dict())
    stage_risks = compute_stage_risks(df.iloc[0].to_dict(), proba)

    return {
        "probability": round(proba * 100, 1),
        "risk_score": risk_score,
        "risk_category": category,
        "estimated_delay_days": est_delay,
        "bottleneck_stage": bottleneck,
        "stage_risks": stage_risks,
        "model_version": "v1.0",
    }


def _infer_bottleneck(row: dict) -> str:
    scores = {
        "Survey & Documentation": (100 - float(row.get("documentation_completion_percentage") or 0)) * 0.8,
        "Objection / Legal Review": float(row.get("legal_risk_index") or 0) if "legal_risk_index" in row else (
            (float(row.get("number_of_active_cases") or 0) * 8)
            + (20 if row.get("court_stay") else 0)
            + (10 if row.get("legal_dispute") else 0)
        ),
        "Compensation Disbursement": (100 - float(row.get("compensation_completion_percentage") or 0)) * 0.9,
        "Rehabilitation & Resettlement": (
            (100 - float(row.get("rehabilitation_completion_percentage") or 100))
            if row.get("rehabilitation_required") else 0
        ),
        "Final Approval / Declaration": float(row.get("pending_approvals") or 0) * 8
            + float(row.get("approval_delay_days") or 0) * 0.2,
        "Ownership Verification": 15 if row.get("ownership_conflict") else 5,
    }
    return max(scores, key=scores.get)


def compute_stage_risks(row: dict, base_proba: float) -> dict:
    """Transparent stage-risk scoring derived from features + base probability."""
    doc = float(row.get("documentation_completion_percentage") or 50)
    comp = float(row.get("compensation_completion_percentage") or 50)
    legal = (
        (float(row.get("number_of_active_cases") or 0) * 12)
        + (25 if row.get("court_stay") else 0)
        + (15 if row.get("legal_dispute") else 0)
        + float(row.get("dispute_severity") or 0) * 5
    )
    pending = float(row.get("pending_approvals") or 0)
    rehab = float(row.get("rehabilitation_completion_percentage") or 100)
    stake = float(row.get("stakeholder_response_rate") or 50)
    base = base_proba * 100

    stages = {
        "Documentation": min(95, max(5, (100 - doc) * 0.7 + base * 0.2)),
        "Ownership Verification": min(95, max(5, (20 if row.get("ownership_conflict") else 8) + base * 0.25)),
        "Legal Review": min(98, max(5, legal * 0.8 + base * 0.15)),
        "Compensation": min(95, max(5, (100 - comp) * 0.75 + base * 0.2)),
        "Rehabilitation": min(95, max(5, ((100 - rehab) * 0.6 if row.get("rehabilitation_required") else 10) + base * 0.1)),
        "Approvals": min(95, max(5, pending * 8 + base * 0.15)),
        "Possession": min(90, max(5, base * 0.4 + (100 - stake) * 0.2)),
    }
    return {k: round(v, 1) for k, v in stages.items()}
