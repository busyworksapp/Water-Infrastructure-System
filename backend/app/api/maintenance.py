from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.alert import Incident
from ..models.maintenance import MaintenanceLog
from ..models.pipeline import Pipeline
from ..models.sensor import Sensor
from ..models.user import User

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


class CreateMaintenanceLogRequest(BaseModel):
    incident_id: Optional[str] = None
    pipeline_id: Optional[str] = None
    sensor_id: Optional[str] = None
    maintenance_type: str
    description: str
    work_performed: Optional[str] = None
    parts_replaced: list = Field(default_factory=list)
    cost: Optional[float] = None
    duration_hours: Optional[float] = None
    scheduled_date: Optional[str] = None
    completed_date: Optional[str] = None


class UpdateMaintenanceLogRequest(BaseModel):
    work_performed: Optional[str] = None
    parts_replaced: Optional[list] = None
    cost: Optional[float] = None
    duration_hours: Optional[float] = None
    completed_date: Optional[str] = None


def _ensure_access(db: Session, user: User, *, sensor_id: Optional[str], pipeline_id: Optional[str], incident_id: Optional[str]):
    if user.is_super_admin:
        return
    municipality_id = user.municipality_id

    if sensor_id:
        sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
        if not sensor or sensor.municipality_id != municipality_id:
            raise HTTPException(status_code=403, detail="Access denied")
    if pipeline_id:
        pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
        if not pipeline or pipeline.municipality_id != municipality_id:
            raise HTTPException(status_code=403, detail="Access denied")
    if incident_id:
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident or incident.municipality_id != municipality_id:
            raise HTTPException(status_code=403, detail="Access denied")


@router.get("/")
async def get_maintenance_logs(
    sensor_id: Optional[str] = None,
    pipeline_id: Optional[str] = None,
    incident_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_access(db, current_user, sensor_id=sensor_id, pipeline_id=pipeline_id, incident_id=incident_id)

    query = db.query(MaintenanceLog)
    if sensor_id:
        query = query.filter(MaintenanceLog.sensor_id == sensor_id)
    if pipeline_id:
        query = query.filter(MaintenanceLog.pipeline_id == pipeline_id)
    if incident_id:
        query = query.filter(MaintenanceLog.incident_id == incident_id)

    if not current_user.is_super_admin:
        query = query.outerjoin(Sensor, MaintenanceLog.sensor_id == Sensor.id).outerjoin(
            Pipeline, MaintenanceLog.pipeline_id == Pipeline.id
        ).outerjoin(Incident, MaintenanceLog.incident_id == Incident.id).filter(
            (Sensor.municipality_id == current_user.municipality_id)
            | (Pipeline.municipality_id == current_user.municipality_id)
            | (Incident.municipality_id == current_user.municipality_id)
        )

    logs = query.order_by(desc(MaintenanceLog.created_at)).limit(limit).all()
    return [
        {
            "id": log.id,
            "incident_id": log.incident_id,
            "pipeline_id": log.pipeline_id,
            "sensor_id": log.sensor_id,
            "maintenance_type": log.maintenance_type,
            "description": log.description,
            "work_performed": log.work_performed,
            "parts_replaced": log.parts_replaced,
            "cost": log.cost,
            "duration_hours": log.duration_hours,
            "scheduled_date": log.scheduled_date.isoformat() if log.scheduled_date else None,
            "completed_date": log.completed_date.isoformat() if log.completed_date else None,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.post("/")
async def create_maintenance_log(
    request: CreateMaintenanceLogRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_access(
        db,
        current_user,
        sensor_id=request.sensor_id,
        pipeline_id=request.pipeline_id,
        incident_id=request.incident_id,
    )

    log = MaintenanceLog(
        incident_id=request.incident_id,
        pipeline_id=request.pipeline_id,
        sensor_id=request.sensor_id,
        performed_by=current_user.id,
        maintenance_type=request.maintenance_type,
        description=request.description,
        work_performed=request.work_performed,
        parts_replaced=request.parts_replaced,
        cost=request.cost,
        duration_hours=request.duration_hours,
        scheduled_date=datetime.fromisoformat(request.scheduled_date) if request.scheduled_date else None,
        completed_date=datetime.fromisoformat(request.completed_date) if request.completed_date else None,
    )

    db.add(log)
    db.commit()
    db.refresh(log)
    return {"id": log.id, "message": "Maintenance log created"}


@router.get("/{log_id}")
async def get_maintenance_log(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = db.query(MaintenanceLog).filter(MaintenanceLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Maintenance log not found")

    _ensure_access(db, current_user, sensor_id=log.sensor_id, pipeline_id=log.pipeline_id, incident_id=log.incident_id)

    return {
        "id": log.id,
        "incident_id": log.incident_id,
        "pipeline_id": log.pipeline_id,
        "sensor_id": log.sensor_id,
        "performed_by": log.performed_by,
        "maintenance_type": log.maintenance_type,
        "description": log.description,
        "work_performed": log.work_performed,
        "parts_replaced": log.parts_replaced,
        "cost": log.cost,
        "duration_hours": log.duration_hours,
        "scheduled_date": log.scheduled_date.isoformat() if log.scheduled_date else None,
        "completed_date": log.completed_date.isoformat() if log.completed_date else None,
        "attachments": log.attachments,
        "metadata": log.metadata_json,
        "created_at": log.created_at.isoformat(),
    }


@router.put("/{log_id}")
async def update_maintenance_log(
    log_id: str,
    request: UpdateMaintenanceLogRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = db.query(MaintenanceLog).filter(MaintenanceLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Maintenance log not found")

    _ensure_access(db, current_user, sensor_id=log.sensor_id, pipeline_id=log.pipeline_id, incident_id=log.incident_id)

    update_data = request.dict(exclude_unset=True)
    if "completed_date" in update_data and update_data["completed_date"]:
        update_data["completed_date"] = datetime.fromisoformat(update_data["completed_date"])

    for field, value in update_data.items():
        setattr(log, field, value)

    log.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Maintenance log updated"}

