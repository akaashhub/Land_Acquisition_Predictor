from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.database import get_db
from app.database.models import Alert

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(
    status: str = None,
    severity: str = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(Alert).order_by(desc(Alert.created_at))
    if status:
        q = q.filter(Alert.status == status)
    if severity:
        q = q.filter(Alert.severity == severity)
    alerts = q.limit(limit).all()
    return {
        "items": [
            {
                "id": a.id,
                "project_id": a.project_id,
                "severity": a.severity,
                "message": a.message,
                "trigger": a.trigger,
                "recommended_action": a.recommended_action,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ],
        "unread_count": db.query(Alert).filter(Alert.status == "unread").count(),
    }


@router.put("/{alert_id}/read")
def mark_read(alert_id: int, db: Session = Depends(get_db)):
    a = db.query(Alert).filter(Alert.id == alert_id).first()
    if not a:
        raise HTTPException(404, "Alert not found")
    a.status = "read"
    db.commit()
    return {"detail": "marked read"}


@router.put("/read-all")
def mark_all_read(db: Session = Depends(get_db)):
    db.query(Alert).filter(Alert.status == "unread").update({"status": "read"})
    db.commit()
    return {"detail": "all marked read"}
