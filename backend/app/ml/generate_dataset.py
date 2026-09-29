"""
Synthetic dataset generator for SIH26017.
Demonstration Dataset — Synthetic Data
Realistic correlations for land acquisition delay prediction.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import random

STAGES = [
    "Proposal / Initial Assessment",
    "Land Identification",
    "Preliminary Notification",
    "Survey & Documentation",
    "Ownership Verification",
    "Objection / Legal Review",
    "Final Approval / Declaration",
    "Compensation Assessment",
    "Compensation Disbursement",
    "Rehabilitation & Resettlement",
    "Possession",
    "Acquisition Closure",
]

PROJECT_TYPES = [
    "Highway", "Railway", "Industrial Corridor", "Irrigation",
    "Power Transmission", "Urban Development", "Airport", "Port",
    "Metro Rail", "Mining", "Defense", "Smart City",
]

STATES = {
    "Maharashtra": ["Pune", "Nagpur", "Nashik", "Aurangabad", "Thane"],
    "Uttar Pradesh": ["Lucknow", "Kanpur", "Agra", "Varanasi", "Meerut"],
    "Karnataka": ["Bengaluru", "Mysuru", "Hubli", "Mangaluru", "Belagavi"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem"],
    "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot", "Gandhinagar"],
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Kota", "Ajmer"],
    "Madhya Pradesh": ["Bhopal", "Indore", "Jabalpur", "Gwalior", "Ujjain"],
    "West Bengal": ["Kolkata", "Howrah", "Durgapur", "Asansol", "Siliguri"],
    "Telangana": ["Hyderabad", "Warangal", "Nizamabad", "Karimnagar", "Khammam"],
    "Bihar": ["Patna", "Gaya", "Muzaffarpur", "Bhagalpur", "Darbhanga"],
}

# Approximate state centroids for realistic lat/lon
STATE_COORDS = {
    "Maharashtra": (19.75, 75.7),
    "Uttar Pradesh": (26.85, 80.9),
    "Karnataka": (15.3, 75.7),
    "Tamil Nadu": (11.1, 78.7),
    "Gujarat": (22.3, 71.2),
    "Rajasthan": (26.9, 75.8),
    "Madhya Pradesh": (23.5, 77.4),
    "West Bengal": (22.6, 88.4),
    "Telangana": (17.9, 79.6),
    "Bihar": (25.6, 85.1),
}


def _risk_score_from_features(row: dict) -> float:
    """Generate a latent risk score with realistic correlations."""
    score = 20.0

    # Legal (strong drivers)
    if row["court_stay"]:
        score += 35
    if row["legal_dispute"]:
        score += 12 + row["number_of_active_cases"] * 4
    score += row["dispute_severity"] * 5
    if row["ownership_conflict"]:
        score += 10
    score += min(row["objection_count"] * 2, 15)

    # Compensation
    comp = row["compensation_completion_percentage"]
    score += max(0, (70 - comp) * 0.35)
    score += min(row["average_compensation_delay"] * 0.15, 12)

    # Documentation
    doc = row["documentation_completion_percentage"]
    score += max(0, (80 - doc) * 0.3)

    # Approvals
    score += min(row["pending_approvals"] * 3.5, 18)
    score += min(row["approval_delay_days"] * 0.08, 10)
    score += min(row["inter_department_dependencies"] * 2, 10)

    # Stakeholders
    score += max(0, (60 - row["stakeholder_response_rate"]) * 0.25)
    score += max(0, (55 - row["landowner_cooperation_score"]) * 0.2)
    score += min(row["unresolved_grievances"] * 2, 12)

    # Progress
    score += max(0, row["progress_variance"] * 0.4)

    # Historical
    score += row["district_historical_delay_rate"] * 25
    score += row["department_historical_delay_rate"] * 15

    # Scale / complexity
    if row["number_of_affected_families"] > 200:
        score += 8
    elif row["number_of_affected_families"] > 50:
        score += 4

    if row["rehabilitation_required"] and row["rehabilitation_completion_percentage"] < 50:
        score += 10
    if row["resettlement_required"] and row["resettlement_completion_percentage"] < 40:
        score += 8

    # Stage pressure (later stages with incomplete work)
    stage_idx = STAGES.index(row["current_stage"]) if row["current_stage"] in STAGES else 0
    if stage_idx >= 5 and doc < 70:
        score += 6
    if stage_idx >= 7 and comp < 60:
        score += 8

    # Noise
    score += np.random.normal(0, 6)
    return float(np.clip(score, 5, 98))


def generate_project(idx: int, force_profile: str | None = None) -> dict:
    state = random.choice(list(STATES.keys()))
    district = random.choice(STATES[state])
    base_lat, base_lon = STATE_COORDS[state]
    lat = base_lat + np.random.uniform(-1.5, 1.5)
    lon = base_lon + np.random.uniform(-1.5, 1.5)

    project_type = random.choice(PROJECT_TYPES)
    stage = random.choice(STAGES)
    stage_idx = STAGES.index(stage)

    start = datetime(2019, 1, 1) + timedelta(days=random.randint(0, 2000))
    planned_days = random.randint(180, 900)
    planned_end = start + timedelta(days=planned_days)
    elapsed = random.randint(30, planned_days + 200)

    total_area = round(np.random.lognormal(4, 1.2), 2)
    acquired_pct = np.clip(np.random.beta(2, 3) * 100, 0, 100)
    if stage_idx >= 10:
        acquired_pct = np.clip(acquired_pct + 40, 0, 100)

    n_landowners = max(1, int(np.random.lognormal(3, 1)))
    n_families = max(0, int(n_landowners * np.random.uniform(0.8, 2.5)))
    n_plots = max(1, int(n_landowners * np.random.uniform(0.9, 1.8)))

    # Correlated risk drivers based on profile
    if force_profile == "critical":
        legal_dispute = True
        court_stay = random.random() < 0.6
        n_cases = random.randint(2, 8)
        dispute_sev = random.randint(3, 5)
        ownership = random.random() < 0.5
        objections = random.randint(5, 20)
        comp_pct = random.uniform(10, 45)
        doc_pct = random.uniform(20, 55)
        pending = random.randint(3, 10)
        stake = random.uniform(15, 40)
        coop = random.uniform(20, 45)
        hist_d = random.uniform(0.4, 0.75)
        grievances = random.randint(5, 25)
    elif force_profile == "high":
        legal_dispute = random.random() < 0.7
        court_stay = random.random() < 0.25
        n_cases = random.randint(1, 4)
        dispute_sev = random.randint(2, 4)
        ownership = random.random() < 0.35
        objections = random.randint(2, 12)
        comp_pct = random.uniform(25, 60)
        doc_pct = random.uniform(30, 65)
        pending = random.randint(2, 7)
        stake = random.uniform(25, 55)
        coop = random.uniform(30, 55)
        hist_d = random.uniform(0.3, 0.6)
        grievances = random.randint(2, 12)
    elif force_profile == "low":
        legal_dispute = random.random() < 0.1
        court_stay = False
        n_cases = 0 if not legal_dispute else 1
        dispute_sev = 0 if not legal_dispute else 1
        ownership = False
        objections = random.randint(0, 2)
        comp_pct = random.uniform(70, 98)
        doc_pct = random.uniform(75, 99)
        pending = random.randint(0, 2)
        stake = random.uniform(70, 95)
        coop = random.uniform(70, 95)
        hist_d = random.uniform(0.1, 0.3)
        grievances = random.randint(0, 3)
    else:
        legal_dispute = random.random() < 0.28
        court_stay = legal_dispute and random.random() < 0.2
        n_cases = random.randint(1, 5) if legal_dispute else 0
        dispute_sev = random.randint(1, 4) if legal_dispute else 0
        ownership = random.random() < 0.15
        objections = random.randint(0, 8)
        comp_pct = float(np.clip(np.random.beta(2.5, 2) * 100, 5, 100))
        doc_pct = float(np.clip(np.random.beta(3, 2) * 100, 10, 100))
        pending = random.randint(0, 8)
        stake = float(np.clip(np.random.beta(3, 2) * 100, 10, 100))
        coop = float(np.clip(np.random.beta(3, 2) * 100, 15, 100))
        hist_d = float(np.clip(np.random.beta(2, 3), 0.05, 0.8))
        grievances = random.randint(0, 15)

    rehab_req = n_families > 20 and random.random() < 0.6
    reset_req = rehab_req and random.random() < 0.5
    rehab_pct = float(np.clip(np.random.beta(2, 3) * 100, 0, 100)) if rehab_req else 100.0
    reset_pct = float(np.clip(np.random.beta(2, 3) * 100, 0, 100)) if reset_req else 100.0

    planned_prog = min(100.0, (elapsed / planned_days) * 100)
    # Actual progress correlates with risk drivers inversely
    lag = (100 - doc_pct) * 0.15 + (100 - comp_pct) * 0.1 + (n_cases * 3)
    actual_prog = float(np.clip(planned_prog - lag + np.random.normal(0, 8), 0, 100))
    progress_var = planned_prog - actual_prog

    comp_assessed = round(total_area * random.uniform(5e5, 2e6), 0)
    comp_disbursed = round(comp_assessed * (comp_pct / 100), 0)

    row = {
        "project_id": f"LA-{1000 + idx:04d}",
        "project_name": f"{project_type} Project {district} Phase-{(idx % 5) + 1}",
        "project_type": project_type,
        "state": state,
        "district": district,
        "latitude": round(lat, 5),
        "longitude": round(lon, 5),
        "project_start_date": start.strftime("%Y-%m-%d"),
        "planned_completion_date": planned_end.strftime("%Y-%m-%d"),
        "current_stage": stage,
        "total_land_area": total_area,
        "acquired_land_area": round(total_area * acquired_pct / 100, 2),
        "remaining_land_area": round(total_area * (1 - acquired_pct / 100), 2),
        "number_of_plots": n_plots,
        "number_of_landowners": n_landowners,
        "number_of_affected_families": n_families,
        "pending_approvals": pending,
        "approval_delay_days": random.randint(0, 120) if pending else random.randint(0, 20),
        "departments_involved": random.randint(2, 8),
        "inter_department_dependencies": random.randint(0, 5),
        "documentation_completion_percentage": round(doc_pct, 1),
        "notification_status": random.choice(["Pending", "Issued", "Completed", "Under Review"]),
        "legal_dispute": legal_dispute,
        "number_of_active_cases": n_cases,
        "dispute_severity": dispute_sev,
        "ownership_conflict": ownership,
        "court_stay": court_stay,
        "objection_count": objections,
        "compensation_assessed": comp_assessed,
        "compensation_disbursed": comp_disbursed,
        "compensation_pending": max(0, comp_assessed - comp_disbursed),
        "compensation_completion_percentage": round(comp_pct, 1),
        "average_compensation_delay": random.randint(0, 90) if comp_pct < 80 else random.randint(0, 20),
        "rehabilitation_required": rehab_req,
        "rehabilitation_completion_percentage": round(rehab_pct, 1),
        "resettlement_required": reset_req,
        "resettlement_completion_percentage": round(reset_pct, 1),
        "stakeholder_response_rate": round(stake, 1),
        "landowner_cooperation_score": round(coop, 1),
        "grievance_count": grievances + random.randint(0, 5),
        "unresolved_grievances": grievances,
        "district_historical_delay_rate": round(hist_d, 3),
        "department_historical_delay_rate": round(float(np.clip(hist_d + np.random.normal(0, 0.1), 0.05, 0.85)), 3),
        "similar_project_average_delay": round(float(np.clip(hist_d * 80 + np.random.normal(0, 15), 5, 150)), 1),
        "planned_progress_percentage": round(planned_prog, 1),
        "actual_progress_percentage": round(actual_prog, 1),
        "progress_variance": round(progress_var, 1),
        "elapsed_days": elapsed,
        "remaining_planned_days": max(0, planned_days - elapsed),
    }

    risk = _risk_score_from_features(row)
    # Soft threshold for delayed label with noise — aim ~40-55% positive class
    delayed = risk > 55 + np.random.normal(0, 10)
    delay_days = 0
    if delayed:
        delay_days = int(np.clip(risk * 1.1 + np.random.normal(0, 15), 5, 250))
    elif risk > 40:
        delay_days = int(np.clip((risk - 35) * 0.7 + np.random.normal(0, 5), 0, 40))

    is_completed = stage_idx >= 10 or (elapsed > planned_days and random.random() < 0.4)

    row.update({
        "delayed": bool(delayed),
        "delay_days": delay_days,
        "delay_stage": stage if delayed else None,
        "is_completed": is_completed,
        "is_demo": False,
        "data_completeness": round(random.uniform(85, 100), 1),
    })
    return row


def generate_demo_projects() -> list[dict]:
    """Carefully designed demo projects for judge demonstration."""
    demos = []

    # LA-1024 — judge demo project (starts medium, can escalate)
    demos.append({
        "project_id": "LA-1024",
        "project_name": "National Highway NH-48 Expansion - Phase 2",
        "project_type": "Highway",
        "state": "Maharashtra",
        "district": "Pune",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "project_start_date": "2023-03-15",
        "planned_completion_date": "2025-09-30",
        "current_stage": "Compensation Disbursement",
        "total_land_area": 245.5,
        "acquired_land_area": 180.2,
        "remaining_land_area": 65.3,
        "number_of_plots": 312,
        "number_of_landowners": 287,
        "number_of_affected_families": 340,
        "pending_approvals": 2,
        "approval_delay_days": 25,
        "departments_involved": 5,
        "inter_department_dependencies": 2,
        "documentation_completion_percentage": 72.0,
        "notification_status": "Completed",
        "legal_dispute": False,
        "number_of_active_cases": 0,
        "dispute_severity": 0,
        "ownership_conflict": False,
        "court_stay": False,
        "objection_count": 3,
        "compensation_assessed": 185000000,
        "compensation_disbursed": 111000000,
        "compensation_pending": 74000000,
        "compensation_completion_percentage": 60.0,
        "average_compensation_delay": 35,
        "rehabilitation_required": True,
        "rehabilitation_completion_percentage": 45.0,
        "resettlement_required": True,
        "resettlement_completion_percentage": 30.0,
        "stakeholder_response_rate": 58.0,
        "landowner_cooperation_score": 55.0,
        "grievance_count": 12,
        "unresolved_grievances": 7,
        "district_historical_delay_rate": 0.38,
        "department_historical_delay_rate": 0.32,
        "similar_project_average_delay": 45.0,
        "planned_progress_percentage": 70.0,
        "actual_progress_percentage": 55.0,
        "progress_variance": 15.0,
        "elapsed_days": 420,
        "remaining_planned_days": 180,
        "delayed": False,
        "delay_days": 0,
        "delay_stage": None,
        "is_completed": False,
        "is_demo": True,
        "data_completeness": 96.0,
    })

    # Critical legal project
    demos.append({
        "project_id": "LA-1101",
        "project_name": "Mumbai-Ahmedabad High Speed Rail Corridor Segment",
        "project_type": "Railway",
        "state": "Gujarat",
        "district": "Ahmedabad",
        "latitude": 23.0225,
        "longitude": 72.5714,
        "project_start_date": "2022-06-01",
        "planned_completion_date": "2024-12-31",
        "current_stage": "Objection / Legal Review",
        "total_land_area": 520.0,
        "acquired_land_area": 210.0,
        "remaining_land_area": 310.0,
        "number_of_plots": 890,
        "number_of_landowners": 750,
        "number_of_affected_families": 920,
        "pending_approvals": 6,
        "approval_delay_days": 95,
        "departments_involved": 7,
        "inter_department_dependencies": 5,
        "documentation_completion_percentage": 48.0,
        "notification_status": "Under Review",
        "legal_dispute": True,
        "number_of_active_cases": 5,
        "dispute_severity": 4,
        "ownership_conflict": True,
        "court_stay": True,
        "objection_count": 18,
        "compensation_assessed": 890000000,
        "compensation_disbursed": 178000000,
        "compensation_pending": 712000000,
        "compensation_completion_percentage": 20.0,
        "average_compensation_delay": 80,
        "rehabilitation_required": True,
        "rehabilitation_completion_percentage": 15.0,
        "resettlement_required": True,
        "resettlement_completion_percentage": 10.0,
        "stakeholder_response_rate": 28.0,
        "landowner_cooperation_score": 25.0,
        "grievance_count": 45,
        "unresolved_grievances": 38,
        "district_historical_delay_rate": 0.55,
        "department_historical_delay_rate": 0.48,
        "similar_project_average_delay": 95.0,
        "planned_progress_percentage": 65.0,
        "actual_progress_percentage": 28.0,
        "progress_variance": 37.0,
        "elapsed_days": 850,
        "remaining_planned_days": 0,
        "delayed": True,
        "delay_days": 120,
        "delay_stage": "Objection / Legal Review",
        "is_completed": False,
        "is_demo": True,
        "data_completeness": 94.0,
    })

    # Low risk
    demos.append({
        "project_id": "LA-1050",
        "project_name": "Bengaluru Outer Ring Road Widening",
        "project_type": "Highway",
        "state": "Karnataka",
        "district": "Bengaluru",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "project_start_date": "2024-01-10",
        "planned_completion_date": "2025-06-30",
        "current_stage": "Compensation Assessment",
        "total_land_area": 45.2,
        "acquired_land_area": 42.0,
        "remaining_land_area": 3.2,
        "number_of_plots": 28,
        "number_of_landowners": 22,
        "number_of_affected_families": 18,
        "pending_approvals": 0,
        "approval_delay_days": 5,
        "departments_involved": 3,
        "inter_department_dependencies": 1,
        "documentation_completion_percentage": 94.0,
        "notification_status": "Completed",
        "legal_dispute": False,
        "number_of_active_cases": 0,
        "dispute_severity": 0,
        "ownership_conflict": False,
        "court_stay": False,
        "objection_count": 0,
        "compensation_assessed": 45000000,
        "compensation_disbursed": 40500000,
        "compensation_pending": 4500000,
        "compensation_completion_percentage": 90.0,
        "average_compensation_delay": 8,
        "rehabilitation_required": False,
        "rehabilitation_completion_percentage": 100.0,
        "resettlement_required": False,
        "resettlement_completion_percentage": 100.0,
        "stakeholder_response_rate": 88.0,
        "landowner_cooperation_score": 92.0,
        "grievance_count": 1,
        "unresolved_grievances": 0,
        "district_historical_delay_rate": 0.18,
        "department_historical_delay_rate": 0.15,
        "similar_project_average_delay": 12.0,
        "planned_progress_percentage": 60.0,
        "actual_progress_percentage": 58.0,
        "progress_variance": 2.0,
        "elapsed_days": 280,
        "remaining_planned_days": 200,
        "delayed": False,
        "delay_days": 0,
        "delay_stage": None,
        "is_completed": False,
        "is_demo": True,
        "data_completeness": 99.0,
    })

    # Compensation delay focused
    demos.append({
        "project_id": "LA-1088",
        "project_name": "Chennai Metro Phase-3 Corridor Extension",
        "project_type": "Metro Rail",
        "state": "Tamil Nadu",
        "district": "Chennai",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "project_start_date": "2023-08-01",
        "planned_completion_date": "2026-03-31",
        "current_stage": "Compensation Disbursement",
        "total_land_area": 78.5,
        "acquired_land_area": 50.0,
        "remaining_land_area": 28.5,
        "number_of_plots": 156,
        "number_of_landowners": 140,
        "number_of_affected_families": 210,
        "pending_approvals": 3,
        "approval_delay_days": 40,
        "departments_involved": 4,
        "inter_department_dependencies": 2,
        "documentation_completion_percentage": 78.0,
        "notification_status": "Completed",
        "legal_dispute": False,
        "number_of_active_cases": 0,
        "dispute_severity": 0,
        "ownership_conflict": False,
        "court_stay": False,
        "objection_count": 4,
        "compensation_assessed": 320000000,
        "compensation_disbursed": 96000000,
        "compensation_pending": 224000000,
        "compensation_completion_percentage": 30.0,
        "average_compensation_delay": 65,
        "rehabilitation_required": True,
        "rehabilitation_completion_percentage": 40.0,
        "resettlement_required": False,
        "resettlement_completion_percentage": 100.0,
        "stakeholder_response_rate": 42.0,
        "landowner_cooperation_score": 38.0,
        "grievance_count": 22,
        "unresolved_grievances": 18,
        "district_historical_delay_rate": 0.42,
        "department_historical_delay_rate": 0.35,
        "similar_project_average_delay": 55.0,
        "planned_progress_percentage": 55.0,
        "actual_progress_percentage": 35.0,
        "progress_variance": 20.0,
        "elapsed_days": 450,
        "remaining_planned_days": 400,
        "delayed": True,
        "delay_days": 45,
        "delay_stage": "Compensation Disbursement",
        "is_completed": False,
        "is_demo": True,
        "data_completeness": 95.0,
    })

    # Documentation bottleneck
    demos.append({
        "project_id": "LA-1075",
        "project_name": "Indore Smart City Land Pooling Zone-B",
        "project_type": "Smart City",
        "state": "Madhya Pradesh",
        "district": "Indore",
        "latitude": 22.7196,
        "longitude": 75.8577,
        "project_start_date": "2023-11-01",
        "planned_completion_date": "2025-12-31",
        "current_stage": "Survey & Documentation",
        "total_land_area": 120.0,
        "acquired_land_area": 30.0,
        "remaining_land_area": 90.0,
        "number_of_plots": 420,
        "number_of_landowners": 380,
        "number_of_affected_families": 450,
        "pending_approvals": 4,
        "approval_delay_days": 55,
        "departments_involved": 6,
        "inter_department_dependencies": 4,
        "documentation_completion_percentage": 35.0,
        "notification_status": "Issued",
        "legal_dispute": False,
        "number_of_active_cases": 0,
        "dispute_severity": 0,
        "ownership_conflict": True,
        "court_stay": False,
        "objection_count": 9,
        "compensation_assessed": 0,
        "compensation_disbursed": 0,
        "compensation_pending": 0,
        "compensation_completion_percentage": 5.0,
        "average_compensation_delay": 0,
        "rehabilitation_required": True,
        "rehabilitation_completion_percentage": 0.0,
        "resettlement_required": True,
        "resettlement_completion_percentage": 0.0,
        "stakeholder_response_rate": 48.0,
        "landowner_cooperation_score": 50.0,
        "grievance_count": 8,
        "unresolved_grievances": 6,
        "district_historical_delay_rate": 0.40,
        "department_historical_delay_rate": 0.36,
        "similar_project_average_delay": 60.0,
        "planned_progress_percentage": 40.0,
        "actual_progress_percentage": 18.0,
        "progress_variance": 22.0,
        "elapsed_days": 330,
        "remaining_planned_days": 420,
        "delayed": True,
        "delay_days": 30,
        "delay_stage": "Survey & Documentation",
        "is_completed": False,
        "is_demo": True,
        "data_completeness": 88.0,
    })

    # More varied demos
    profiles = ["critical", "high", "high", "low", "low", "medium", "medium",
                "critical", "high", "low", "medium", "high", "low", "medium"]
    for i, p in enumerate(profiles):
        if p == "medium":
            p = None
        row = generate_project(2000 + i, force_profile=p)
        row["project_id"] = f"LA-{1200 + i:04d}"
        row["is_demo"] = True
        demos.append(row)

    return demos


def generate_dataset(n_samples: int = 3000, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)
    random.seed(seed)

    rows = []
    # Force class balance profiles
    n_critical = int(n_samples * 0.12)
    n_high = int(n_samples * 0.20)
    n_low = int(n_samples * 0.25)
    n_rest = n_samples - n_critical - n_high - n_low

    idx = 0
    for _ in range(n_critical):
        rows.append(generate_project(idx, "critical"))
        idx += 1
    for _ in range(n_high):
        rows.append(generate_project(idx, "high"))
        idx += 1
    for _ in range(n_low):
        rows.append(generate_project(idx, "low"))
        idx += 1
    for _ in range(n_rest):
        rows.append(generate_project(idx, None))
        idx += 1

    # Add demo projects
    demos = generate_demo_projects()
    # Avoid ID collision
    existing_ids = {r["project_id"] for r in rows}
    for d in demos:
        if d["project_id"] not in existing_ids:
            rows.append(d)

    df = pd.DataFrame(rows)
    return df


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "data" / "sample_dataset.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df = generate_dataset(3000)
    df.to_csv(out, index=False)
    print(f"Generated {len(df)} records → {out}")
    print(f"Delayed rate: {df['delayed'].mean():.2%}")
    print(f"Risk proxy (delay_days>0): {(df['delay_days'] > 0).mean():.2%}")
    print(df["current_stage"].value_counts().head())
