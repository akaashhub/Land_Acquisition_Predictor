"""Feature engineering — same pipeline for training and inference."""
from __future__ import annotations

import pandas as pd
import numpy as np

FEATURE_COLUMNS = [
    "pending_approvals",
    "approval_delay_days",
    "departments_involved",
    "inter_department_dependencies",
    "documentation_completion_percentage",
    "legal_dispute",
    "number_of_active_cases",
    "dispute_severity",
    "ownership_conflict",
    "court_stay",
    "objection_count",
    "compensation_completion_percentage",
    "average_compensation_delay",
    "rehabilitation_required",
    "rehabilitation_completion_percentage",
    "resettlement_required",
    "resettlement_completion_percentage",
    "stakeholder_response_rate",
    "landowner_cooperation_score",
    "grievance_count",
    "unresolved_grievances",
    "district_historical_delay_rate",
    "department_historical_delay_rate",
    "similar_project_average_delay",
    "planned_progress_percentage",
    "actual_progress_percentage",
    "progress_variance",
    "elapsed_days",
    "remaining_planned_days",
    "number_of_landowners",
    "number_of_affected_families",
    "number_of_plots",
    "total_land_area",
    # engineered
    "compensation_gap",
    "documentation_gap",
    "approval_pressure",
    "legal_risk_index",
    "stakeholder_risk",
    "rehabilitation_gap",
    "historical_delay_index",
    "acquisition_completion_percentage",
    "coordination_complexity",
    "days_remaining_ratio",
]

CATEGORICAL_RAW = ["project_type", "state", "current_stage", "notification_status"]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features. Safe for both train and predict."""
    out = df.copy()

    out["compensation_gap"] = 100.0 - out.get("compensation_completion_percentage", 0).fillna(0)
    out["documentation_gap"] = 100.0 - out.get("documentation_completion_percentage", 0).fillna(0)
    out["approval_pressure"] = (
        out.get("pending_approvals", 0).fillna(0) * 2
        + out.get("approval_delay_days", 0).fillna(0) * 0.1
        + out.get("inter_department_dependencies", 0).fillna(0)
    )
    out["legal_risk_index"] = (
        out.get("number_of_active_cases", 0).fillna(0) * 3
        + out.get("dispute_severity", 0).fillna(0) * 4
        + out.get("objection_count", 0).fillna(0) * 0.5
        + out.get("court_stay", 0).fillna(0).astype(float) * 20
        + out.get("legal_dispute", 0).fillna(0).astype(float) * 8
        + out.get("ownership_conflict", 0).fillna(0).astype(float) * 6
    )
    out["stakeholder_risk"] = (
        (100 - out.get("stakeholder_response_rate", 50).fillna(50)) * 0.4
        + (100 - out.get("landowner_cooperation_score", 50).fillna(50)) * 0.3
        + out.get("unresolved_grievances", 0).fillna(0) * 1.5
    )
    rehab_req = out.get("rehabilitation_required", False)
    if not isinstance(rehab_req, pd.Series):
        rehab_req = pd.Series([rehab_req] * len(out))
    out["rehabilitation_gap"] = np.where(
        rehab_req.fillna(False).astype(bool),
        100 - out.get("rehabilitation_completion_percentage", 0).fillna(0),
        0,
    )
    out["historical_delay_index"] = (
        out.get("district_historical_delay_rate", 0.3).fillna(0.3) * 50
        + out.get("department_historical_delay_rate", 0.3).fillna(0.3) * 30
        + out.get("similar_project_average_delay", 30).fillna(30) * 0.2
    )
    total = out.get("total_land_area", 1).fillna(1).replace(0, 1)
    acquired = out.get("acquired_land_area", 0).fillna(0)
    out["acquisition_completion_percentage"] = (acquired / total * 100).clip(0, 100)
    out["coordination_complexity"] = (
        np.log1p(out.get("number_of_landowners", 1).fillna(1))
        + np.log1p(out.get("number_of_affected_families", 0).fillna(0))
        + out.get("departments_involved", 1).fillna(1) * 0.5
    )
    remaining = out.get("remaining_planned_days", 90).fillna(90)
    elapsed = out.get("elapsed_days", 1).fillna(1).replace(0, 1)
    out["days_remaining_ratio"] = remaining / (elapsed + remaining)

    # Boolean to int
    for col in ["legal_dispute", "ownership_conflict", "court_stay",
                "rehabilitation_required", "resettlement_required"]:
        if col in out.columns:
            out[col] = out[col].fillna(False).astype(int)

    return out


def get_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    eng = engineer_features(df)
    cols = [c for c in FEATURE_COLUMNS if c in eng.columns]
    X = eng[cols].copy()
    for c in X.columns:
        X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0)
    return X
