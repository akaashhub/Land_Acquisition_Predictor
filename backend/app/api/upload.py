from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import pandas as pd
import io

from app.database.database import get_db
from app.database.models import Project
from app.services.prediction_service import run_full_prediction
from app.api.auth import require_roles
from app.database.models import User

router = APIRouter(prefix="/api/upload", tags=["upload"])

REQUIRED_COLS = ["project_id", "project_name", "project_type", "state", "district", "current_stage"]
OPTIONAL_NUMERIC = [
    "total_land_area", "acquired_land_area", "remaining_land_area",
    "number_of_plots", "number_of_landowners", "number_of_affected_families",
    "pending_approvals", "approval_delay_days", "departments_involved",
    "inter_department_dependencies", "documentation_completion_percentage",
    "number_of_active_cases", "dispute_severity", "objection_count",
    "compensation_assessed", "compensation_disbursed", "compensation_pending",
    "compensation_completion_percentage", "average_compensation_delay",
    "rehabilitation_completion_percentage", "resettlement_completion_percentage",
    "stakeholder_response_rate", "landowner_cooperation_score",
    "grievance_count", "unresolved_grievances",
    "district_historical_delay_rate", "department_historical_delay_rate",
    "similar_project_average_delay", "planned_progress_percentage",
    "actual_progress_percentage", "progress_variance", "elapsed_days",
    "remaining_planned_days", "latitude", "longitude",
]
BOOL_COLS = ["legal_dispute", "ownership_conflict", "court_stay",
             "rehabilitation_required", "resettlement_required"]


@router.post("/csv")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("ADMIN")),
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files are accepted")

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(400, f"Invalid CSV: {e}")

    total_rows = len(df)
    missing_required = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing_required:
        raise HTTPException(
            400,
            f"Missing required columns: {missing_required}. "
            f"Found columns: {list(df.columns)}",
        )

    valid = 0
    invalid = 0
    errors = []
    imported = []
    missing_field_stats = {}

    for idx, row in df.iterrows():
        try:
            data = {"project_id": str(row["project_id"]),
                    "project_name": str(row["project_name"]),
                    "project_type": str(row["project_type"]),
                    "state": str(row["state"]),
                    "district": str(row["district"]),
                    "current_stage": str(row.get("current_stage", "Proposal"))}

            missing = []
            for c in OPTIONAL_NUMERIC:
                if c in df.columns and pd.notna(row.get(c)):
                    data[c] = float(row[c])
                else:
                    missing.append(c)
                    missing_field_stats[c] = missing_field_stats.get(c, 0) + 1

            for c in BOOL_COLS:
                if c in df.columns and pd.notna(row.get(c)):
                    val = row[c]
                    data[c] = bool(val) if not isinstance(val, str) else val.lower() in ("1", "true", "yes")

            completeness = max(0, 100 - len(missing) * 2)
            data["data_completeness"] = completeness

            existing = db.query(Project).filter(Project.project_id == data["project_id"]).first()
            if existing:
                for k, v in data.items():
                    if k != "project_id":
                        setattr(existing, k, v)
                p = existing
            else:
                p = Project(**data)
                db.add(p)
            db.flush()
            run_full_prediction(db, p, create_alert=False)
            valid += 1
            imported.append(data["project_id"])
        except Exception as e:
            invalid += 1
            errors.append({"row": int(idx) + 2, "error": str(e)})

    db.commit()

    confidence_note = None
    if missing_field_stats:
        top_missing = sorted(missing_field_stats.items(), key=lambda x: -x[1])[:5]
        confidence_note = (
            "Prediction confidence may be reduced because important project information is missing. "
            f"Most frequent missing fields: {[m[0] for m in top_missing]}"
        )

    return {
        "total_rows": total_rows,
        "valid_rows": valid,
        "invalid_rows": invalid,
        "imported_project_ids": imported[:20],
        "errors": errors[:10],
        "missing_field_stats": missing_field_stats,
        "confidence_note": confidence_note,
        "disclaimer": "Demonstration Dataset — Synthetic Data handling applies to uploaded rows as well.",
    }


@router.get("/sample-csv")
def sample_csv_info():
    return {
        "required_columns": REQUIRED_COLS,
        "optional_numeric": OPTIONAL_NUMERIC,
        "boolean_columns": BOOL_COLS,
        "download_path": "/api/upload/sample-csv/download",
    }
