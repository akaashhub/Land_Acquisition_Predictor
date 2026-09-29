"""Explainability — feature contribution style explanations."""
from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd

from app.ml.feature_engineering import engineer_features
from app.ml.predict import project_to_df, get_models


# Human-readable labels and direction
FACTOR_META = {
    "court_stay": ("Active court stay order", "risk", 25),
    "legal_dispute": ("Active legal dispute", "risk", 12),
    "number_of_active_cases": ("Number of active legal cases", "risk", 4),
    "dispute_severity": ("Dispute severity level", "risk", 5),
    "ownership_conflict": ("Ownership conflict present", "risk", 10),
    "objection_count": ("Landowner objections filed", "risk", 1.5),
    "compensation_completion_percentage": ("Compensation completion", "protective", -0.35),
    "compensation_gap": ("Compensation still pending", "risk", 0.35),
    "average_compensation_delay": ("Average compensation delay (days)", "risk", 0.12),
    "documentation_completion_percentage": ("Documentation completion", "protective", -0.3),
    "documentation_gap": ("Incomplete documentation", "risk", 0.3),
    "pending_approvals": ("Pending inter-department approvals", "risk", 3.5),
    "approval_delay_days": ("Approval process delay (days)", "risk", 0.08),
    "inter_department_dependencies": ("Inter-department dependencies", "risk", 2),
    "stakeholder_response_rate": ("Stakeholder response rate", "protective", -0.25),
    "landowner_cooperation_score": ("Landowner cooperation", "protective", -0.2),
    "unresolved_grievances": ("Unresolved grievances", "risk", 2),
    "grievance_count": ("Total grievances", "risk", 0.5),
    "progress_variance": ("Progress lag vs plan", "risk", 0.4),
    "district_historical_delay_rate": ("District historical delay rate", "risk", 25),
    "department_historical_delay_rate": ("Department historical delay rate", "risk", 15),
    "similar_project_average_delay": ("Similar project average delay", "risk", 0.15),
    "rehabilitation_gap": ("Rehabilitation incomplete", "risk", 0.25),
    "legal_risk_index": ("Composite legal risk index", "risk", 0.8),
    "stakeholder_risk": ("Composite stakeholder risk", "risk", 0.5),
    "approval_pressure": ("Approval pressure index", "risk", 0.4),
    "historical_delay_index": ("Historical delay index", "risk", 0.3),
    "coordination_complexity": ("Coordination complexity", "risk", 1.5),
    "number_of_affected_families": ("Affected families count", "risk", 0.02),
}


def explain_project(project: dict | Any, top_k: int = 6) -> dict:
    """Return top risk factors and protective factors with human text."""
    df = project_to_df(project)
    eng = engineer_features(df)
    row = eng.iloc[0].to_dict()

    contributions = []
    for feat, (label, kind, weight) in FACTOR_META.items():
        if feat not in row:
            continue
        val = row[feat]
        try:
            val = float(val)
        except (TypeError, ValueError):
            continue

        if kind == "risk":
            # Higher value → higher risk contribution
            if feat in ("court_stay", "legal_dispute", "ownership_conflict"):
                contrib = weight if val > 0.5 else 0
            else:
                contrib = val * weight
            if contrib > 1.5:
                contributions.append({
                    "feature": feat,
                    "label": label,
                    "value": val,
                    "contribution": round(contrib, 1),
                    "direction": "risk",
                    "text": _human_text(feat, val, label, "risk"),
                })
        else:  # protective — high values reduce risk
            # contribution magnitude of protection
            if feat.endswith("_percentage") or feat.endswith("_rate") or feat.endswith("_score"):
                protection = max(0, (val - 50) * abs(weight))
                if protection > 2:
                    contributions.append({
                        "feature": feat,
                        "label": label,
                        "value": val,
                        "contribution": round(protection, 1),
                        "direction": "protective",
                        "text": _human_text(feat, val, label, "protective"),
                    })

    risks = sorted([c for c in contributions if c["direction"] == "risk"],
                   key=lambda x: -x["contribution"])[:top_k]
    protects = sorted([c for c in contributions if c["direction"] == "protective"],
                      key=lambda x: -x["contribution"])[:4]

    # Try model-based importance if available
    try:
        clf, _, prep = get_models()
        if hasattr(clf, "feature_importances_"):
            names = prep.feature_names
            imps = clf.feature_importances_
            model_fi = sorted(
                [{"feature": n, "importance": round(float(i), 4)} for n, i in zip(names, imps)],
                key=lambda x: -x["importance"]
            )[:10]
        else:
            model_fi = []
    except Exception:
        model_fi = []

    return {
        "top_risk_factors": risks,
        "protective_factors": protects,
        "model_feature_importance": model_fi,
    }


def _human_text(feat: str, val: float, label: str, direction: str) -> str:
    if feat == "court_stay" and val > 0.5:
        return "A court stay order is active, substantially elevating delay risk."
    if feat == "legal_dispute" and val > 0.5:
        return "Active legal dispute(s) are increasing the likelihood of delay."
    if feat == "ownership_conflict" and val > 0.5:
        return "Ownership conflicts require resolution before acquisition can proceed smoothly."
    if feat == "number_of_active_cases":
        return f"{int(val)} active legal case(s) are contributing to project risk."
    if feat == "compensation_completion_percentage" or feat == "compensation_gap":
        if direction == "risk":
            pct = val if feat == "compensation_completion_percentage" else 100 - val
            if feat == "compensation_gap":
                pct = 100 - val if val < 100 else val
            # better: use gap
            gap = val if feat == "compensation_gap" else 100 - val
            return f"Compensation is only partially complete (gap ~{gap:.0f}%), increasing delay likelihood."
        return f"Compensation is {val:.0f}% complete, which helps reduce delay risk."
    if feat == "documentation_gap" or feat == "documentation_completion_percentage":
        if direction == "risk":
            gap = val if feat == "documentation_gap" else 100 - val
            return f"Documentation is incomplete (gap ~{gap:.0f}%), raising process risk."
        return f"Documentation is {val:.0f}% complete, a protective factor."
    if feat == "pending_approvals":
        return f"{int(val)} pending approval(s) are creating administrative bottleneck risk."
    if feat == "stakeholder_response_rate":
        if direction == "protective":
            return f"Stakeholder response rate is healthy at {val:.0f}%."
        return f"Low stakeholder response rate ({val:.0f}%) increases coordination risk."
    if feat == "unresolved_grievances":
        return f"{int(val)} unresolved grievance(s) may escalate into delays."
    if feat == "progress_variance":
        return f"Actual progress lags planned progress by approximately {val:.0f} percentage points."
    if feat == "district_historical_delay_rate":
        return f"This district has a historical delay rate of {val*100:.0f}%, elevating baseline risk."
    if feat == "rehabilitation_gap":
        return f"Rehabilitation progress has a gap of ~{val:.0f}%, affecting possession readiness."
    return f"{label}: {val:.1f}"
