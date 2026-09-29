from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database.database import get_db
from app.database.models import Project, Prediction

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _latest_predictions_subq(db: Session):
    """Get latest prediction per project via window-like approach."""
    # SQLite-friendly: get all predictions ordered, then keep latest in Python for simplicity
    preds = (
        db.query(Prediction)
        .order_by(Prediction.project_id, desc(Prediction.created_at))
        .all()
    )
    latest = {}
    for p in preds:
        if p.project_id not in latest:
            latest[p.project_id] = p
    return latest


@router.get("/overview")
def overview(db: Session = Depends(get_db)):
    total = db.query(Project).count()
    latest = _latest_predictions_subq(db)

    on_track = medium = high = critical = 0
    total_delay = 0.0
    total_risk = 0.0
    n = 0
    for pid, pred in latest.items():
        cat = pred.risk_category
        if cat == "LOW":
            on_track += 1
        elif cat == "MEDIUM":
            medium += 1
        elif cat == "HIGH":
            high += 1
        elif cat == "CRITICAL":
            critical += 1
        total_delay += pred.estimated_delay_days or 0
        total_risk += pred.risk_score or 0
        n += 1

    delayed_count = db.query(Project).filter(Project.delayed == True).count()  # noqa

    return {
        "total_projects": total,
        "on_track": on_track,
        "medium_risk": medium,
        "high_risk": high,
        "critical_risk": critical,
        "average_predicted_delay": round(total_delay / n, 1) if n else 0,
        "average_risk_score": round(total_risk / n, 1) if n else 0,
        "delayed_count": delayed_count,
        "predictions_count": n,
        "disclaimer": "Demonstration Dataset — Synthetic Data. Prototype risk thresholds.",
    }


@router.get("/states")
def by_state(db: Session = Depends(get_db)):
    latest = _latest_predictions_subq(db)
    projects = db.query(Project).all()
    by_state = {}
    for p in projects:
        s = p.state
        if s not in by_state:
            by_state[s] = {"state": s, "projects": 0, "high_risk": 0, "critical": 0,
                           "total_risk": 0.0, "total_delay": 0.0, "n_pred": 0}
        by_state[s]["projects"] += 1
        pred = latest.get(p.project_id)
        if pred:
            by_state[s]["total_risk"] += pred.risk_score
            by_state[s]["total_delay"] += pred.estimated_delay_days or 0
            by_state[s]["n_pred"] += 1
            if pred.risk_category == "HIGH":
                by_state[s]["high_risk"] += 1
            elif pred.risk_category == "CRITICAL":
                by_state[s]["critical"] += 1

    result = []
    for s, v in by_state.items():
        n = v["n_pred"] or 1
        result.append({
            "state": s,
            "projects": v["projects"],
            "high_risk": v["high_risk"],
            "critical": v["critical"],
            "average_risk": round(v["total_risk"] / n, 1),
            "average_delay": round(v["total_delay"] / n, 1),
        })
    result.sort(key=lambda x: -x["average_risk"])
    return {"items": result, "note": "Highest-risk areas in the demonstration dataset."}


@router.get("/districts")
def by_district(state: str = None, db: Session = Depends(get_db)):
    latest = _latest_predictions_subq(db)
    q = db.query(Project)
    if state:
        q = q.filter(Project.state == state)
    projects = q.all()
    by_d = {}
    for p in projects:
        key = f"{p.state}|{p.district}"
        if key not in by_d:
            by_d[key] = {"state": p.state, "district": p.district, "projects": 0,
                         "high_risk": 0, "critical": 0, "total_risk": 0.0,
                         "total_delay": 0.0, "n_pred": 0}
        by_d[key]["projects"] += 1
        pred = latest.get(p.project_id)
        if pred:
            by_d[key]["total_risk"] += pred.risk_score
            by_d[key]["total_delay"] += pred.estimated_delay_days or 0
            by_d[key]["n_pred"] += 1
            if pred.risk_category == "HIGH":
                by_d[key]["high_risk"] += 1
            elif pred.risk_category == "CRITICAL":
                by_d[key]["critical"] += 1

    result = []
    for v in by_d.values():
        n = v["n_pred"] or 1
        result.append({
            "state": v["state"],
            "district": v["district"],
            "projects": v["projects"],
            "high_risk": v["high_risk"],
            "critical": v["critical"],
            "average_risk": round(v["total_risk"] / n, 1),
            "average_delay": round(v["total_delay"] / n, 1),
        })
    result.sort(key=lambda x: -x["average_risk"])
    return {"items": result[:50], "note": "Highest-risk areas in the demonstration dataset."}


@router.get("/risk-distribution")
def risk_distribution(db: Session = Depends(get_db)):
    latest = _latest_predictions_subq(db)
    dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    probs = []
    for pred in latest.values():
        dist[pred.risk_category] = dist.get(pred.risk_category, 0) + 1
        probs.append(pred.probability)
    # Histogram bins
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    hist = {f"{bins[i]}-{bins[i+1]}": 0 for i in range(len(bins) - 1)}
    for pr in probs:
        for i in range(len(bins) - 1):
            if bins[i] <= pr < bins[i + 1] or (i == len(bins) - 2 and pr == 100):
                hist[f"{bins[i]}-{bins[i+1]}"] += 1
                break
    return {"by_category": dist, "probability_histogram": hist}


@router.get("/stage-bottlenecks")
def stage_bottlenecks(db: Session = Depends(get_db)):
    latest = _latest_predictions_subq(db)
    counts = {}
    for pred in latest.values():
        if pred.risk_category in ("HIGH", "CRITICAL") and pred.bottleneck_stage:
            counts[pred.bottleneck_stage] = counts.get(pred.bottleneck_stage, 0) + 1
    items = [{"stage": k, "count": v} for k, v in counts.items()]
    items.sort(key=lambda x: -x["count"])
    return {"items": items}


@router.get("/predicted-vs-actual")
def predicted_vs_actual(db: Session = Depends(get_db)):
    """For completed projects with known delay_days."""
    completed = db.query(Project).filter(Project.is_completed == True).limit(200).all()  # noqa
    latest = _latest_predictions_subq(db)
    points = []
    for p in completed:
        pred = latest.get(p.project_id)
        if pred:
            points.append({
                "project_id": p.project_id,
                "predicted_delay": pred.estimated_delay_days,
                "actual_delay": p.delay_days,
                "state": p.state,
            })
    return {"items": points, "note": "Based on synthetic demonstration outcomes."}


@router.get("/map")
def map_data(db: Session = Depends(get_db)):
    latest = _latest_predictions_subq(db)
    projects = db.query(Project).filter(
        Project.latitude.isnot(None), Project.longitude.isnot(None)
    ).all()
    items = []
    for p in projects:
        pred = latest.get(p.project_id)
        items.append({
            "project_id": p.project_id,
            "project_name": p.project_name,
            "state": p.state,
            "district": p.district,
            "latitude": p.latitude,
            "longitude": p.longitude,
            "project_type": p.project_type,
            "current_stage": p.current_stage,
            "risk_score": pred.risk_score if pred else None,
            "risk_category": pred.risk_category if pred else "UNKNOWN",
            "delay_probability": pred.probability if pred else None,
            "bottleneck_stage": pred.bottleneck_stage if pred else None,
        })
    return {"items": items}
