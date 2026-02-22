from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.alert import Incident, IncidentStatus, AlertSeverity

router = APIRouter(prefix="/incidents", tags=["Incidents"])

class CreateIncidentRequest(BaseModel):
    title: str
    description: str
    incident_type: str
    severity: str
    municipality_id: str
    pipeline_id: Optional[str] = None
    alert_id: Optional[str] = None

@router.post("/")
async def create_incident(
    request: CreateIncidentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_super_admin and request.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")

    incident = Incident(
        title=request.title,
        description=request.description,
        incident_type=request.incident_type,
        severity=AlertSeverity[request.severity.upper()],
        municipality_id=request.municipality_id,
        pipeline_id=request.pipeline_id,
        alert_id=request.alert_id,
        reported_by=current_user.id,
        status=IncidentStatus.REPORTED
    )
    
    db.add(incident)
    db.commit()
    db.refresh(incident)
    
    return {"id": incident.id, "message": "Incident created successfully"}

@router.get("/")
async def get_incidents(
    municipality_id: Optional[str] = None,
    status: Optional[IncidentStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Incident)
    
    if not current_user.is_super_admin:
        query = query.filter(Incident.municipality_id == current_user.municipality_id)
    elif municipality_id:
        query = query.filter(Incident.municipality_id == municipality_id)
    
    if status:
        query = query.filter(Incident.status == status)
    
    incidents = query.order_by(Incident.created_at.desc()).limit(100).all()
    
    return [{
        "id": i.id,
        "title": i.title,
        "description": i.description,
        "incident_type": i.incident_type,
        "status": i.status.value,
        "severity": i.severity.value,
        "created_at": i.created_at.isoformat()
    } for i in incidents]

