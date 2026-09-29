"""Early warning / alert generation."""
from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from app.database.models import Alert


def create_alerts_for_prediction(
    db: Session,
    project_id: str,
    prediction: dict,
    previous_prediction: dict | None = None,
    project: dict | Any | None = None,
) -> list[Alert]:
    alerts = []
    score = prediction["risk_score"]
    cat = prediction["risk_category"]

    if cat == "CRITICAL":
        alerts.append(Alert(
            project_id=project_id,
            severity="CRITICAL",
            message=f"Project {project_id} entered CRITICAL RISK status (score {score}).",
            trigger="risk_category_critical",
            recommended_action="Immediate review of legal, compensation, and documentation drivers.",
            status="unread",
        ))
    elif cat == "HIGH":
        if not previous_prediction or previous_prediction.get("risk_category") not in ("HIGH", "CRITICAL"):
            alerts.append(Alert(
                project_id=project_id,
                severity="HIGH",
                message=f"Project {project_id} entered HIGH RISK status (score {score}).",
                trigger="risk_category_high",
                recommended_action="Review top risk factors and initiate recommended interventions.",
                status="unread",
            ))

    if previous_prediction:
        prev = previous_prediction.get("risk_score", 0)
        delta = score - prev
        if delta >= 15:
            alerts.append(Alert(
                project_id=project_id,
                severity="WARNING" if delta < 25 else "HIGH",
                message=f"Risk increased: {prev} → {score} (+{delta:.0f} points) for {project_id}.",
                trigger="risk_increase",
                recommended_action="Investigate recent changes and top risk drivers.",
                status="unread",
            ))

    if prediction.get("probability", 0) >= 70:
        if not previous_prediction or previous_prediction.get("probability", 0) < 70:
            alerts.append(Alert(
                project_id=project_id,
                severity="HIGH",
                message=f"Delay probability exceeds 70% for project {project_id}.",
                trigger="probability_threshold",
                recommended_action="Prioritize bottleneck stage interventions.",
                status="unread",
            ))

    if project is not None:
        p = project if isinstance(project, dict) else {
            c.name: getattr(project, c.name, None) for c in project.__table__.columns
        }
        if p.get("court_stay"):
            alerts.append(Alert(
                project_id=project_id,
                severity="CRITICAL",
                message=f"Court stay active on project {project_id}.",
                trigger="court_stay",
                recommended_action="Prioritize legal review and dispute resolution.",
                status="unread",
            ))
        if (p.get("unresolved_grievances") or 0) >= 15:
            alerts.append(Alert(
                project_id=project_id,
                severity="WARNING",
                message=f"High unresolved grievances ({p.get('unresolved_grievances')}) on {project_id}.",
                trigger="grievance_spike",
                recommended_action="Conduct grievance redressal meetings.",
                status="unread",
            ))

    for a in alerts:
        db.add(a)
    if alerts:
        db.commit()
        for a in alerts:
            db.refresh(a)
    return alerts
