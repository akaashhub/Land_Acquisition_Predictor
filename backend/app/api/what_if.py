from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.models import Project
from app.schemas import WhatIfRequest
from app.services.what_if_service import run_what_if

router = APIRouter(prefix="/api/projects", tags=["what-if"])


@router.post("/{project_id}/what-if")
def what_if(project_id: str, body: WhatIfRequest, db: Session = Depends(get_db)):
    p = db.query(Project).filter(Project.project_id == project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")
    return run_what_if(p, body.changes)
