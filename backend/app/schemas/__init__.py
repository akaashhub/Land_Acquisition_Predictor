from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class LoginRequest(BaseModel):
    username: str
    password: str


class ProjectBase(BaseModel):
    project_id: str
    project_name: str
    project_type: str
    state: str
    district: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    current_stage: str = "Proposal"
    total_land_area: float = 0
    acquired_land_area: float = 0
    remaining_land_area: float = 0
    number_of_plots: int = 0
    number_of_landowners: int = 0
    number_of_affected_families: int = 0
    pending_approvals: int = 0
    approval_delay_days: int = 0
    departments_involved: int = 1
    inter_department_dependencies: int = 0
    documentation_completion_percentage: float = 0
    notification_status: str = "Pending"
    legal_dispute: bool = False
    number_of_active_cases: int = 0
    dispute_severity: int = 0
    ownership_conflict: bool = False
    court_stay: bool = False
    objection_count: int = 0
    compensation_assessed: float = 0
    compensation_disbursed: float = 0
    compensation_pending: float = 0
    compensation_completion_percentage: float = 0
    average_compensation_delay: int = 0
    rehabilitation_required: bool = False
    rehabilitation_completion_percentage: float = 0
    resettlement_required: bool = False
    resettlement_completion_percentage: float = 0
    stakeholder_response_rate: float = 50
    landowner_cooperation_score: float = 50
    grievance_count: int = 0
    unresolved_grievances: int = 0
    district_historical_delay_rate: float = 0.3
    department_historical_delay_rate: float = 0.3
    similar_project_average_delay: float = 30
    planned_progress_percentage: float = 0
    actual_progress_percentage: float = 0
    progress_variance: float = 0
    elapsed_days: int = 0
    remaining_planned_days: int = 90
    project_start_date: Optional[str] = None
    planned_completion_date: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    compensation_completion_percentage: Optional[float] = None
    documentation_completion_percentage: Optional[float] = None
    pending_approvals: Optional[int] = None
    approval_delay_days: Optional[int] = None
    legal_dispute: Optional[bool] = None
    number_of_active_cases: Optional[int] = None
    dispute_severity: Optional[int] = None
    ownership_conflict: Optional[bool] = None
    court_stay: Optional[bool] = None
    objection_count: Optional[int] = None
    stakeholder_response_rate: Optional[float] = None
    landowner_cooperation_score: Optional[float] = None
    unresolved_grievances: Optional[int] = None
    grievance_count: Optional[int] = None
    rehabilitation_completion_percentage: Optional[float] = None
    resettlement_completion_percentage: Optional[float] = None
    progress_variance: Optional[float] = None
    actual_progress_percentage: Optional[float] = None
    current_stage: Optional[str] = None
    average_compensation_delay: Optional[int] = None


class ProjectOut(ProjectBase):
    id: int
    delayed: bool = False
    delay_days: int = 0
    is_completed: bool = False
    is_demo: bool = False
    data_completeness: float = 100
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # latest prediction (optional join)
    risk_score: Optional[float] = None
    risk_category: Optional[str] = None
    delay_probability: Optional[float] = None
    estimated_delay_days: Optional[float] = None
    bottleneck_stage: Optional[str] = None

    class Config:
        from_attributes = True


class PredictionOut(BaseModel):
    probability: float
    risk_score: float
    risk_category: str
    estimated_delay_days: float
    bottleneck_stage: Optional[str] = None
    stage_risks: Optional[Dict[str, float]] = None
    top_risk_factors: Optional[List[Dict[str, Any]]] = None
    protective_factors: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    model_version: str = "v1.0"
    alerts_generated: int = 0


class WhatIfRequest(BaseModel):
    changes: Dict[str, Any]


class AlertOut(BaseModel):
    id: int
    project_id: str
    severity: str
    message: str
    trigger: Optional[str] = None
    recommended_action: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OverviewAnalytics(BaseModel):
    total_projects: int
    on_track: int
    medium_risk: int
    high_risk: int
    critical_risk: int
    average_predicted_delay: float
    average_risk_score: float
    delayed_count: int


class Message(BaseModel):
    detail: str
