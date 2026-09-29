"""Orchestrates prediction, explanation, recommendations, persistence."""
from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session

from app.database.models import Project, Prediction, Recommendation
from app.ml.predict import predict_project
from app.ml.explain import explain_project
from app.services.recommendation_service import generate_recommendations
from app.services.alert_service import create_alerts_for_prediction


def run_full_prediction(db: Session, project: Project, create_alert: bool = True) -> dict:
    pred = predict_project(project)
    explanation = explain_project(project)
    recs = generate_recommendations(project, pred)

    # Previous prediction for delta alerts
    prev = (
        db.query(Prediction)
        .filter(Prediction.project_id == project.project_id)
        .order_by(Prediction.created_at.desc())
        .first()
    )
    prev_dict = None
    if prev:
        prev_dict = {
            "risk_score": prev.risk_score,
            "risk_category": prev.risk_category,
            "probability": prev.probability,
        }

    prediction_row = Prediction(
        project_id=project.project_id,
        probability=pred["probability"],
        risk_score=pred["risk_score"],
        risk_category=pred["risk_category"],
        estimated_delay_days=pred["estimated_delay_days"],
        bottleneck_stage=pred["bottleneck_stage"],
        stage_risks=pred["stage_risks"],
        top_risk_factors=explanation["top_risk_factors"],
        protective_factors=explanation["protective_factors"],
        model_version=pred["model_version"],
    )
    db.add(prediction_row)

    # Refresh recommendations
    db.query(Recommendation).filter(Recommendation.project_id == project.project_id).delete()
    for r in recs:
        db.add(Recommendation(
            project_id=project.project_id,
            category=r["category"],
            recommendation=r["recommendation"],
            priority=r["priority"],
        ))
    db.commit()
    db.refresh(prediction_row)

    alerts = []
    if create_alert:
        alerts = create_alerts_for_prediction(
            db, project.project_id, pred, prev_dict, project
        )

    return {
        **pred,
        "top_risk_factors": explanation["top_risk_factors"],
        "protective_factors": explanation["protective_factors"],
        "recommendations": recs,
        "alerts_generated": len(alerts),
        "prediction_id": prediction_row.id,
    }
