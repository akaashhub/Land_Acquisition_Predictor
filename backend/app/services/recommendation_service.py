"""Actionable recommendation engine from project conditions."""
from __future__ import annotations

from typing import Any


def generate_recommendations(project: dict | Any, prediction: dict | None = None) -> list[dict]:
    if hasattr(project, "__table__"):
        p = {c.name: getattr(project, c.name, None) for c in project.__table__.columns}
    else:
        p = dict(project)

    recs = []

    # Legal
    if p.get("court_stay"):
        recs.append({
            "category": "Legal",
            "priority": 1,
            "recommendation": (
                "Court stay is active. Prioritize legal review, engage specialized counsel, "
                "and establish a dedicated dispute-resolution workflow with the court liaison."
            ),
        })
    elif p.get("legal_dispute") or (p.get("number_of_active_cases") or 0) > 0:
        recs.append({
            "category": "Legal",
            "priority": 1,
            "recommendation": (
                f"There are {p.get('number_of_active_cases') or 0} active legal case(s). "
                "Prioritize legal review and establish a dedicated dispute-resolution workflow."
            ),
        })
    if p.get("ownership_conflict"):
        recs.append({
            "category": "Legal",
            "priority": 1,
            "recommendation": (
                "Ownership conflict detected. Accelerate ownership verification with revenue records "
                "and consider alternate dispute resolution for contested parcels."
            ),
        })

    # Compensation
    comp = float(p.get("compensation_completion_percentage") or 0)
    if comp < 50:
        recs.append({
            "category": "Compensation",
            "priority": 1,
            "recommendation": (
                f"Compensation is only {comp:.0f}% complete. Prioritize compensation verification "
                "and disbursement for pending landowners; set weekly disbursement targets."
            ),
        })
    elif comp < 75:
        recs.append({
            "category": "Compensation",
            "priority": 2,
            "recommendation": (
                f"Compensation at {comp:.0f}%. Clear remaining pending disbursements and "
                "address average compensation delays to avoid further slippage."
            ),
        })

    # Documentation
    doc = float(p.get("documentation_completion_percentage") or 0)
    if doc < 60:
        recs.append({
            "category": "Documentation",
            "priority": 1,
            "recommendation": (
                f"Documentation is only {doc:.0f}% complete. Assign additional documentation "
                "resources and resolve incomplete ownership records on a priority basis."
            ),
        })
    elif doc < 80:
        recs.append({
            "category": "Documentation",
            "priority": 2,
            "recommendation": (
                f"Documentation at {doc:.0f}%. Close remaining gaps in survey and ownership "
                "records before advancing to the next stage."
            ),
        })

    # Approvals
    pending = int(p.get("pending_approvals") or 0)
    if pending >= 3:
        recs.append({
            "category": "Approvals",
            "priority": 1,
            "recommendation": (
                f"{pending} approvals are pending. Escalate inter-departmental dependencies "
                "to the designated coordinating authority and schedule a joint clearance meeting."
            ),
        })
    elif pending >= 1:
        recs.append({
            "category": "Approvals",
            "priority": 2,
            "recommendation": (
                f"{pending} pending approval(s). Follow up with concerned departments "
                "and set clear response deadlines."
            ),
        })

    # Stakeholders
    stake = float(p.get("stakeholder_response_rate") or 50)
    if stake < 45:
        recs.append({
            "category": "Stakeholders",
            "priority": 1,
            "recommendation": (
                f"Stakeholder response rate is low ({stake:.0f}%). Initiate targeted stakeholder "
                "communication and grievance-resolution meetings at the village/ward level."
            ),
        })
    unresolved = int(p.get("unresolved_grievances") or 0)
    if unresolved >= 5:
        recs.append({
            "category": "Grievances",
            "priority": 1 if unresolved >= 10 else 2,
            "recommendation": (
                f"{unresolved} unresolved grievances. Conduct focused grievance redressal camps "
                "and publish resolution timelines to rebuild trust."
            ),
        })

    # Rehabilitation
    if p.get("rehabilitation_required"):
        rehab = float(p.get("rehabilitation_completion_percentage") or 0)
        if rehab < 50:
            recs.append({
                "category": "Rehabilitation",
                "priority": 1 if rehab < 30 else 2,
                "recommendation": (
                    f"Rehabilitation is only {rehab:.0f}% complete. Accelerate rehabilitation "
                    "and resettlement packages for affected families before seeking possession."
                ),
            })

    # Progress
    variance = float(p.get("progress_variance") or 0)
    if variance > 20:
        recs.append({
            "category": "Progress",
            "priority": 2,
            "recommendation": (
                f"Progress lags plan by ~{variance:.0f} points. Review critical path activities "
                "and reallocate resources to bottleneck stages."
            ),
        })

    if not recs:
        recs.append({
            "category": "Monitoring",
            "priority": 3,
            "recommendation": (
                "No critical risk drivers detected. Continue routine monitoring and "
                "maintain current documentation and compensation pace."
            ),
        })

    recs.sort(key=lambda r: r["priority"])
    return recs
