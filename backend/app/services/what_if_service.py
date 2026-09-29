"""What-If simulation — modify variables and re-predict without saving."""
from __future__ import annotations

from typing import Any
from copy import deepcopy

from app.ml.predict import predict_project, project_to_df
from app.ml.explain import explain_project
from app.services.recommendation_service import generate_recommendations


SIMULATABLE_FIELDS = [
    "compensation_completion_percentage",
    "documentation_completion_percentage",
    "pending_approvals",
    "approval_delay_days",
    "legal_dispute",
    "number_of_active_cases",
    "dispute_severity",
    "ownership_conflict",
    "court_stay",
    "objection_count",
    "stakeholder_response_rate",
    "landowner_cooperation_score",
    "unresolved_grievances",
    "grievance_count",
    "rehabilitation_completion_percentage",
    "resettlement_completion_percentage",
    "progress_variance",
    "average_compensation_delay",
]


def run_what_if(project: dict | Any, changes: dict) -> dict:
    if hasattr(project, "__table__"):
        base = {c.name: getattr(project, c.name, None) for c in project.__table__.columns}
    else:
        base = dict(project)

    original_pred = predict_project(base)
    original_explain = explain_project(base)

    simulated = deepcopy(base)
    applied = {}
    for k, v in changes.items():
        if k in SIMULATABLE_FIELDS:
            # type coercion
            if k in ("legal_dispute", "ownership_conflict", "court_stay"):
                v = bool(v)
            elif k in ("pending_approvals", "number_of_active_cases", "dispute_severity",
                       "objection_count", "unresolved_grievances", "grievance_count",
                       "approval_delay_days", "average_compensation_delay"):
                v = int(v)
            else:
                v = float(v)
            applied[k] = {"from": base.get(k), "to": v}
            simulated[k] = v

    # Recompute derived simple fields
    if "compensation_completion_percentage" in applied:
        assessed = float(simulated.get("compensation_assessed") or 0)
        pct = float(simulated["compensation_completion_percentage"])
        simulated["compensation_disbursed"] = assessed * pct / 100
        simulated["compensation_pending"] = max(0, assessed - simulated["compensation_disbursed"])

    sim_pred = predict_project(simulated)
    sim_explain = explain_project(simulated)
    sim_recs = generate_recommendations(simulated, sim_pred)

    risk_change = round(original_pred["risk_score"] - sim_pred["risk_score"], 1)

    return {
        "original": original_pred,
        "simulated": sim_pred,
        "risk_change": risk_change,
        "risk_reduction": max(0, risk_change),
        "changed_variables": applied,
        "original_risk_factors": original_explain["top_risk_factors"][:5],
        "simulated_risk_factors": sim_explain["top_risk_factors"][:5],
        "recommendations": sim_recs[:5],
        "disclaimer": (
            "Simulation results are model-based estimates and not guaranteed outcomes. "
            "Predictions support, not replace, administrative judgment."
        ),
    }
