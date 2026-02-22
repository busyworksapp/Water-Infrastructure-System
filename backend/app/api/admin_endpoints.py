"""Admin Panel API Endpoints for System Management"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import (
    User, Municipality, AlertRule, Sensor, SensorType,
    Protocol, Pipeline, MaintenanceTask
)
from app.schemas.admin import (
    SensorTypeCreate, SensorTypeUpdate,
    ProtocolCreate, ProtocolUpdate,
    PipelineCreate, PipelineUpdate,
    AlertRuleCreate, AlertRuleUpdate,
)
from app.utils.error_handling import (
    ForbiddenError, NotFoundError, ValidationException
)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def verify_admin(current_user: User = Depends(get_current_user)) -> User:
    """Verify user is admin"""
    if not current_user.is_super_admin:
        raise ForbiddenError("Admin access required")
    return current_user


# ==================== Sensor Types Management ====================

@router.get("/sensor-types")
async def list_sensor_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> dict:
    """List all sensor types"""
    types = db.query(SensorType).offset(skip).limit(limit).all()
    total = db.query(SensorType).count()
    
    return {
        "success": True,
        "data": {
            "sensor_types": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "unit": t.unit,
                    "min_value": t.min_value,
                    "max_value": t.max_value,
                }
                for t in types
            ],
            "total": total,
        },
    }


@router.post("/sensor-types")
async def create_sensor_type(
    payload: SensorTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin),
) -> dict:
    """Create a new sensor type"""
    # Check if already exists
    existing = db.query(SensorType).filter(SensorType.name == payload.name).first()
    if existing:
        raise ValidationException(f"Sensor type '{payload.name}' already exists")
    
    sensor_type = SensorType(
        name=payload.name,
        description=payload.description,
        unit=payload.unit,
        min_value=payload.min_value,
        max_value=payload.max_value,
    )
    db.add(sensor_type)
    db.commit()
    db.refresh(sensor_type)
    
    return {
        "success": True,
        "message": f"Sensor type '{payload.name}' created",
        "data": {"id": sensor_type.id, "name": sensor_type.name},
    }


@router.put("/sensor-types/{type_id}")
async def update_sensor_type(
    type_id: int,
    payload: SensorTypeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin),
) -> dict:
    """Update a sensor type"""
    sensor_type = db.query(SensorType).filter(SensorType.id == type_id).first()
    if not sensor_type:
        raise NotFoundError(f"Sensor type {type_id} not found")
    
    if payload.name:
        sensor_type.name = payload.name
    if payload.description:
        sensor_type.description = payload.description
    if payload.unit:
        sensor_type.unit = payload.unit
    if payload.min_value is not None:
        sensor_type.min_value = payload.min_value
    if payload.max_value is not None:
        sensor_type.max_value = payload.max_value
    
    db.commit()
    db.refresh(sensor_type)
    
    return {
        "success": True,
        "message": "Sensor type updated",
        "data": {"id": sensor_type.id},
    }


@router.delete("/sensor-types/{type_id}")
async def delete_sensor_type(
    type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin),
) -> dict:
    """Delete a sensor type"""
    sensor_type = db.query(SensorType).filter(SensorType.id == type_id).first()
    if not sensor_type:
        raise NotFoundError(f"Sensor type {type_id} not found")
    
    db.delete(sensor_type)
    db.commit()
    
    return {
        "success": True,
        "message": "Sensor type deleted",
    }


# ==================== Protocols Management ====================

@router.get("/protocols")
async def list_protocols(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> dict:
    """List all IoT protocols"""
    protocols = db.query(Protocol).offset(skip).limit(limit).all()
    total = db.query(Protocol).count()
    
    return {
        "success": True,
        "data": {
            "protocols": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "port": p.port,
                    "is_active": p.is_active,
                }
                for p in protocols
            ],
            "total": total,
        },
    }


@router.post("/protocols")
async def create_protocol(
    payload: ProtocolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin),
) -> dict:
    """Create a new IoT protocol"""
    existing = db.query(Protocol).filter(Protocol.name == payload.name).first()
    if existing:
        raise ValidationException(f"Protocol '{payload.name}' already exists")
    
    protocol = Protocol(
        name=payload.name,
        description=payload.description,
        port=payload.port,
        is_active=True,
    )
    db.add(protocol)
    db.commit()
    db.refresh(protocol)
    
    return {
        "success": True,
        "message": f"Protocol '{payload.name}' created",
        "data": {"id": protocol.id},
    }


@router.put("/protocols/{protocol_id}")
async def update_protocol(
    protocol_id: int,
    payload: ProtocolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin),
) -> dict:
    """Update a protocol"""
    protocol = db.query(Protocol).filter(Protocol.id == protocol_id).first()
    if not protocol:
        raise NotFoundError(f"Protocol {protocol_id} not found")
    
    if payload.name:
        protocol.name = payload.name
    if payload.description:
        protocol.description = payload.description
    if payload.port:
        protocol.port = payload.port
    if payload.is_active is not None:
        protocol.is_active = payload.is_active
    
    db.commit()
    db.refresh(protocol)
    
    return {
        "success": True,
        "message": "Protocol updated",
        "data": {"id": protocol.id},
    }


# ==================== Pipelines Management ====================

@router.get("/pipelines")
async def list_pipelines(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin),
    municipality_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> dict:
    """List all water pipelines"""
    query = db.query(Pipeline)
    if municipality_id:
        query = query.filter(Pipeline.municipality_id == municipality_id)
    
    pipelines = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "success": True,
        "data": {
            "pipelines": [
                {
                    "id": p.id,
                    "name": p.name,
                    "diameter": p.diameter,
                    "material": p.material,
                    "length": p.length,
                    "status": p.status,
                }
                for p in pipelines
            ],
            "total": total,
        },
    }


@router.post("/pipelines")
async def create_pipeline(
    payload: PipelineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin),
) -> dict:
    """Create a new pipeline"""
    # Verify municipality exists
    municipality = db.query(Municipality).filter(
        Municipality.id == payload.municipality_id
    ).first()
    if not municipality:
        raise ValidationException(f"Municipality {payload.municipality_id} not found")
    
    pipeline = Pipeline(
        name=payload.name,
        diameter=payload.diameter,
        material=payload.material,
        length=payload.length,
        municipality_id=payload.municipality_id,
        status="operational",
    )
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    
    return {
        "success": True,
        "message": f"Pipeline '{payload.name}' created",
        "data": {"id": pipeline.id},
    }


# ==================== Alert Rules Management ====================

@router.get("/alert-rules")
async def list_alert_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin),
    municipality_id: Optional[int] = Query(None),
    sensor_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> dict:
    """List alert rules"""
    query = db.query(AlertRule)
    
    if municipality_id:
        query = query.filter(AlertRule.municipality_id == municipality_id)
    if sensor_type:
        query = query.filter(AlertRule.sensor_type == sensor_type)
    if is_active is not None:
        query = query.filter(AlertRule.is_active == is_active)
    
    rules = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "success": True,
        "data": {
            "rules": [
                {
                    "id": r.id,
                    "name": r.name,
                    "sensor_type": r.sensor_type,
                    "threshold_min": r.threshold_min,
                    "threshold_max": r.threshold_max,
                    "is_active": r.is_active,
                }
                for r in rules
            ],
            "total": total,
        },
    }


@router.post("/alert-rules")
async def create_alert_rule(
    payload: AlertRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin),
) -> dict:
    """Create a new alert rule"""
    rule = AlertRule(
        name=payload.name,
        description=payload.description,
        sensor_type=payload.sensor_type,
        rule_type=payload.rule_type,
        threshold_min=payload.threshold_min,
        threshold_max=payload.threshold_max,
        municipality_id=payload.municipality_id,
        is_active=True,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return {
        "success": True,
        "message": f"Alert rule '{payload.name}' created",
        "data": {"id": rule.id},
    }


@router.put("/alert-rules/{rule_id}")
async def update_alert_rule(
    rule_id: int,
    payload: AlertRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin),
) -> dict:
    """Update an alert rule"""
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not rule:
        raise NotFoundError(f"Alert rule {rule_id} not found")
    
    if payload.name:
        rule.name = payload.name
    if payload.threshold_min is not None:
        rule.threshold_min = payload.threshold_min
    if payload.threshold_max is not None:
        rule.threshold_max = payload.threshold_max
    if payload.is_active is not None:
        rule.is_active = payload.is_active
    
    db.commit()
    db.refresh(rule)
    
    return {
        "success": True,
        "message": "Alert rule updated",
        "data": {"id": rule.id},
    }


# ==================== Maintenance Management ====================

@router.get("/maintenance-tasks")
async def list_maintenance_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> dict:
    """List maintenance tasks"""
    query = db.query(MaintenanceTask)
    if status:
        query = query.filter(MaintenanceTask.status == status)
    
    tasks = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "success": True,
        "data": {
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "scheduled_date": t.scheduled_date.isoformat() if t.scheduled_date else None,
                    "priority": t.priority,
                }
                for t in tasks
            ],
            "total": total,
        },
    }


@router.post("/maintenance-tasks")
async def create_maintenance_task(
    title: str,
    description: str,
    scheduled_date: datetime,
    priority: str = "medium",
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin),
) -> dict:
    """Create a maintenance task"""
    task = MaintenanceTask(
        title=title,
        description=description,
        scheduled_date=scheduled_date,
        priority=priority,
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    return {
        "success": True,
        "message": "Maintenance task created",
        "data": {"id": task.id},
    }


# ==================== System Configuration ====================

@router.get("/system-config")
async def get_system_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin),
) -> dict:
    """Get system configuration"""
    from app.core.config import settings
    
    return {
        "success": True,
        "data": {
            "app_name": settings.APP_NAME,
            "app_version": settings.APP_VERSION,
            "debug": settings.DEBUG,
            "environment": settings.ENVIRONMENT,
            "timezone": "UTC",
            "max_upload_size": "100MB",
            "backup_enabled": True,
            "backup_frequency": "daily",
        },
    }
