from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
)
from sqlalchemy.sql import func
from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    role = Column(String(20), default="VIEWER")  # ADMIN, OFFICER, VIEWER
    full_name = Column(String(128), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(32), unique=True, index=True, nullable=False)
    project_name = Column(String(256), nullable=False)
    project_type = Column(String(64), nullable=False)
    state = Column(String(64), nullable=False, index=True)
    district = Column(String(64), nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    project_start_date = Column(String(32), nullable=True)
    planned_completion_date = Column(String(32), nullable=True)
    current_stage = Column(String(64), nullable=False, default="Proposal")

    # Land
    total_land_area = Column(Float, default=0.0)
    acquired_land_area = Column(Float, default=0.0)
    remaining_land_area = Column(Float, default=0.0)
    number_of_plots = Column(Integer, default=0)
    number_of_landowners = Column(Integer, default=0)
    number_of_affected_families = Column(Integer, default=0)

    # Administrative
    pending_approvals = Column(Integer, default=0)
    approval_delay_days = Column(Integer, default=0)
    departments_involved = Column(Integer, default=1)
    inter_department_dependencies = Column(Integer, default=0)
    documentation_completion_percentage = Column(Float, default=0.0)
    notification_status = Column(String(32), default="Pending")

    # Legal
    legal_dispute = Column(Boolean, default=False)
    number_of_active_cases = Column(Integer, default=0)
    dispute_severity = Column(Integer, default=0)  # 0-5
    ownership_conflict = Column(Boolean, default=False)
    court_stay = Column(Boolean, default=False)
    objection_count = Column(Integer, default=0)

    # Compensation
    compensation_assessed = Column(Float, default=0.0)
    compensation_disbursed = Column(Float, default=0.0)
    compensation_pending = Column(Float, default=0.0)
    compensation_completion_percentage = Column(Float, default=0.0)
    average_compensation_delay = Column(Integer, default=0)

    # Rehabilitation
    rehabilitation_required = Column(Boolean, default=False)
    rehabilitation_completion_percentage = Column(Float, default=0.0)
    resettlement_required = Column(Boolean, default=False)
    resettlement_completion_percentage = Column(Float, default=0.0)

    # Stakeholders
    stakeholder_response_rate = Column(Float, default=50.0)
    landowner_cooperation_score = Column(Float, default=50.0)
    grievance_count = Column(Integer, default=0)
    unresolved_grievances = Column(Integer, default=0)

    # Historical
    district_historical_delay_rate = Column(Float, default=0.3)
    department_historical_delay_rate = Column(Float, default=0.3)
    similar_project_average_delay = Column(Float, default=30.0)

    # Progress
    planned_progress_percentage = Column(Float, default=0.0)
    actual_progress_percentage = Column(Float, default=0.0)
    progress_variance = Column(Float, default=0.0)
    elapsed_days = Column(Integer, default=0)
    remaining_planned_days = Column(Integer, default=90)

    # Targets (ground truth for completed / historical)
    delayed = Column(Boolean, default=False)
    delay_days = Column(Integer, default=0)
    delay_stage = Column(String(64), nullable=True)
    is_completed = Column(Boolean, default=False)
    is_demo = Column(Boolean, default=False)

    # Meta
    data_completeness = Column(Float, default=100.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(32), ForeignKey("projects.project_id"), index=True, nullable=False)
    probability = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    risk_category = Column(String(20), nullable=False)
    estimated_delay_days = Column(Float, default=0.0)
    bottleneck_stage = Column(String(64), nullable=True)
    stage_risks = Column(JSON, nullable=True)
    top_risk_factors = Column(JSON, nullable=True)
    protective_factors = Column(JSON, nullable=True)
    model_version = Column(String(32), default="v1.0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProjectUpdate(Base):
    __tablename__ = "project_updates"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(32), ForeignKey("projects.project_id"), index=True, nullable=False)
    changed_fields = Column(JSON, nullable=False)
    previous_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    previous_risk = Column(Float, nullable=True)
    new_risk = Column(Float, nullable=True)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(32), ForeignKey("projects.project_id"), index=True, nullable=False)
    severity = Column(String(20), nullable=False)  # INFO, WARNING, HIGH, CRITICAL
    message = Column(Text, nullable=False)
    trigger = Column(String(128), nullable=True)
    recommended_action = Column(Text, nullable=True)
    status = Column(String(20), default="unread")  # unread, read
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(String(32), ForeignKey("projects.project_id"), index=True, nullable=False)
    category = Column(String(64), nullable=False)
    recommendation = Column(Text, nullable=False)
    priority = Column(Integer, default=2)  # 1=high, 2=medium, 3=low
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ModelMetrics(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(64), nullable=False)
    model_type = Column(String(32), nullable=False)  # classifier / regressor
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    roc_auc = Column(Float, nullable=True)
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    r2 = Column(Float, nullable=True)
    feature_importance = Column(JSON, nullable=True)
    confusion_matrix = Column(JSON, nullable=True)
    training_size = Column(Integer, nullable=True)
    n_features = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
