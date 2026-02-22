from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from geoalchemy2.shape import to_shape
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.alert import Alert, AlertStatus, AlertSeverity


def _get_coords(geom):
    if not geom:
        return None
    try:
        shape = to_shape(geom)
        return [shape.x, shape.y]
    except Exception:
        return None

router = APIRouter(prefix="/alerts", tags=["Alerts"])

class AcknowledgeAlertRequest(BaseModel):
    notes: Optional[str] = None

class ResolveAlertRequest(BaseModel):
    resolution_notes: str

@router.get("/")
async def get_alerts(
    municipality_id: Optional[str] = None,
    status: Optional[AlertStatus] = None,
    severity: Optional[AlertSeverity] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Alert)
    
    if not current_user.is_super_admin:
        query = query.filter(Alert.municipality_id == current_user.municipality_id)
    elif municipality_id:
        query = query.filter(Alert.municipality_id == municipality_id)
    
    if status:
        query = query.filter(Alert.status == status)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    
    alerts = query.order_by(desc(Alert.created_at)).limit(limit).all()
    
    return [{
        "id": a.id,
        "alert_type": a.alert_type.value,
        "severity": a.severity.value,
        "status": a.status.value,
        "title": a.title,
        "description": a.description,
        "sensor_id": a.sensor_id,
        "pipeline_id": a.pipeline_id,
        "municipality_id": a.municipality_id,
        "location": {
            "type": "Point",
            "coordinates": _get_coords(a.location)
        },
        "triggered_value": a.triggered_value,
        "created_at": a.created_at.isoformat(),
        "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
        "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None
    } for a in alerts]

@router.get("/{alert_id}")
async def get_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if not current_user.is_super_admin and alert.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {
        "id": alert.id,
        "alert_type": alert.alert_type.value,
        "severity": alert.severity.value,
        "status": alert.status.value,
        "title": alert.title,
        "description": alert.description,
        "sensor_id": alert.sensor_id,
        "pipeline_id": alert.pipeline_id,
        "municipality_id": alert.municipality_id,
        "location": {
            "type": "Point",
            "coordinates": _get_coords(alert.location)
        },
        "triggered_value": alert.triggered_value,
        "threshold_value": alert.threshold_value,
        "resolution_notes": alert.resolution_notes,
        "metadata": alert.metadata_json,
        "created_at": alert.created_at.isoformat(),
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
    }

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    request: AcknowledgeAlertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if not current_user.is_super_admin and alert.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    
    if request.notes:
        alert.metadata_json = alert.metadata_json or {}
        alert.metadata_json['acknowledgement_notes'] = request.notes
    
    db.commit()
    
    return {"message": "Alert acknowledged successfully"}

@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    request: ResolveAlertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    if not current_user.is_super_admin and alert.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    alert.status = AlertStatus.RESOLVED
    alert.resolved_by = current_user.id
    alert.resolved_at = datetime.utcnow()
    alert.resolution_notes = request.resolution_notes
    
    db.commit()
    
    return {"message": "Alert resolved successfully"}

@router.get("/statistics/summary")
async def get_alert_statistics(
    municipality_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Alert)
    
    if not current_user.is_super_admin:
        query = query.filter(Alert.municipality_id == current_user.municipality_id)
    elif municipality_id:
        query = query.filter(Alert.municipality_id == municipality_id)
    
    total = query.count()
    open_alerts = query.filter(Alert.status == AlertStatus.OPEN).count()
    critical = query.filter(Alert.severity == AlertSeverity.CRITICAL).count()
    high = query.filter(Alert.severity == AlertSeverity.HIGH).count()
    
    return {
        "total": total,
        "open": open_alerts,
        "critical": critical,
        "high": high
    }

