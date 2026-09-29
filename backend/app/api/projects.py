from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.database import get_db
from app.database.models import Project, Prediction, ProjectUpdate, Recommendation
from app.schemas import ProjectOut, ProjectCreate, ProjectUpdate as ProjectUpdateSchema, PredictionOut
from app.services.prediction_service import run_full_prediction
from app.api.auth import get_current_user, require_roles
from app.database.models import User

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _attach_prediction(db: Session, p: Project) -> dict:
    data = {c.name: getattr(p, c.name) for c in p.__table__.columns}
    pred = (
        db.query(Prediction)
        .filter(Prediction.project_id == p.project_id)
        .order_by(desc(Prediction.created_at))
        .first()
    )
    if pred:
        data["risk_score"] = pred.risk_score
        data["risk_category"] = pred.risk_category
        data["delay_probability"] = pred.probability
        data["estimated_delay_days"] = pred.estimated_delay_days
        data["bottleneck_stage"] = pred.bottleneck_stage
    return data


@router.get("")
def list_projects(
    state: Optional[str] = None,
    district: Optional[str] = None,
    risk: Optional[str] = None,
    stage: Optional[str] = None,
    project_type: Optional[str] = None,
    search: Optional[str] = None,
    demo_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    sort_by: str = "risk_score",
    sort_dir: str = "desc",
    db: Session = Depends(get_db),
):
    q = db.query(Project)
    if state:
        q = q.filter(Project.state == state)
    if district:
        q = q.filter(Project.district == district)
    if stage:
        q = q.filter(Project.current_stage == stage)
    if project_type:
        q = q.filter(Project.project_type == project_type)
    if demo_only:
        q = q.filter(Project.is_demo == True)  # noqa: E712
    if search:
        like = f"%{search}%"
        q = q.filter(
            (Project.project_id.ilike(like)) | (Project.project_name.ilike(like))
        )

    projects = q.offset(skip).limit(limit * 3).all()  # over-fetch for risk filter
    results = [_attach_prediction(db, p) for p in projects]

    if risk:
        results = [r for r in results if (r.get("risk_category") or "").upper() == risk.upper()]

    reverse = sort_dir.lower() == "desc"
    if sort_by in ("risk_score", "delay_probability", "estimated_delay_days"):
        results.sort(key=lambda x: x.get(sort_by) or 0, reverse=reverse)
    elif sort_by == "project_name":
        results.sort(key=lambda x: x.get("project_name") or "", reverse=reverse)

    total = q.count()
    return {"total": total, "items": results[:limit]}


@router.get("/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.project_id == project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")
    data = _attach_prediction(db, p)

    pred = (
        db.query(Prediction)
        .filter(Prediction.project_id == project_id)
        .order_by(desc(Prediction.created_at))
        .first()
    )
    if pred:
        data["stage_risks"] = pred.stage_risks
        data["top_risk_factors"] = pred.top_risk_factors
        data["protective_factors"] = pred.protective_factors

    recs = (
        db.query(Recommendation)
        .filter(Recommendation.project_id == project_id)
        .order_by(Recommendation.priority)
        .all()
    )
    data["recommendations"] = [
        {"category": r.category, "recommendation": r.recommendation, "priority": r.priority}
        for r in recs
    ]

    history = (
        db.query(Prediction)
        .filter(Prediction.project_id == project_id)
        .order_by(Prediction.created_at)
        .all()
    )
    data["risk_history"] = [
        {
            "risk_score": h.risk_score,
            "risk_category": h.risk_category,
            "probability": h.probability,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in history
    ]

    updates = (
        db.query(ProjectUpdate)
        .filter(ProjectUpdate.project_id == project_id)
        .order_by(desc(ProjectUpdate.created_at))
        .limit(20)
        .all()
    )
    data["updates"] = [
        {
            "changed_fields": u.changed_fields,
            "previous_values": u.previous_values,
            "new_values": u.new_values,
            "previous_risk": u.previous_risk,
            "new_risk": u.new_risk,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in updates
    ]
    return data


@router.post("")
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMIN", "OFFICER")),
):
    existing = db.query(Project).filter(Project.project_id == body.project_id).first()
    if existing:
        raise HTTPException(400, "Project ID already exists")
    p = Project(**body.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    result = run_full_prediction(db, p)
    return {"project": _attach_prediction(db, p), "prediction": result}


@router.put("/{project_id}")
def update_project(
    project_id: str,
    body: ProjectUpdateSchema,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMIN", "OFFICER")),
):
    p = db.query(Project).filter(Project.project_id == project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")

    # Previous risk
    prev_pred = (
        db.query(Prediction)
        .filter(Prediction.project_id == project_id)
        .order_by(desc(Prediction.created_at))
        .first()
    )
    prev_risk = prev_pred.risk_score if prev_pred else None

    changes = body.model_dump(exclude_unset=True)
    previous_values = {}
    new_values = {}
    for k, v in changes.items():
        previous_values[k] = getattr(p, k, None)
        setattr(p, k, v)
        new_values[k] = v

    # Recompute compensation amounts if pct changed
    if "compensation_completion_percentage" in changes:
        assessed = p.compensation_assessed or 0
        p.compensation_disbursed = assessed * (p.compensation_completion_percentage / 100)
        p.compensation_pending = max(0, assessed - p.compensation_disbursed)

    db.add(p)
    db.commit()
    db.refresh(p)

    result = run_full_prediction(db, p, create_alert=True)

    update_row = ProjectUpdate(
        project_id=project_id,
        changed_fields=list(changes.keys()),
        previous_values=previous_values,
        new_values=new_values,
        previous_risk=prev_risk,
        new_risk=result["risk_score"],
        created_by=user.username if user else None,
    )
    db.add(update_row)
    db.commit()

    return {
        "project": _attach_prediction(db, p),
        "prediction": result,
        "risk_change": round((result["risk_score"] - (prev_risk or result["risk_score"])), 1),
        "message": f"Risk {'increased' if result['risk_score'] > (prev_risk or 0) else 'changed'} "
                   f"from {prev_risk} to {result['risk_score']}",
    }


@router.post("/{project_id}/predict")
def predict_endpoint(project_id: str, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.project_id == project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")
    result = run_full_prediction(db, p)
    return result


@router.get("/{project_id}/risk")
def get_risk(project_id: str, db: Session = Depends(get_db)):
    pred = (
        db.query(Prediction)
        .filter(Prediction.project_id == project_id)
        .order_by(desc(Prediction.created_at))
        .first()
    )
    if not pred:
        p = db.query(Project).filter(Project.project_id == project_id).first()
        if not p:
            raise HTTPException(404, "Project not found")
        return run_full_prediction(db, p)
    return {
        "probability": pred.probability,
        "risk_score": pred.risk_score,
        "risk_category": pred.risk_category,
        "estimated_delay_days": pred.estimated_delay_days,
        "bottleneck_stage": pred.bottleneck_stage,
        "stage_risks": pred.stage_risks,
        "top_risk_factors": pred.top_risk_factors,
        "protective_factors": pred.protective_factors,
    }


@router.get("/{project_id}/recommendations")
def get_recommendations(project_id: str, db: Session = Depends(get_db)):
    recs = (
        db.query(Recommendation)
        .filter(Recommendation.project_id == project_id)
        .order_by(Recommendation.priority)
        .all()
    )
    return [
        {"category": r.category, "recommendation": r.recommendation, "priority": r.priority}
        for r in recs
    ]
