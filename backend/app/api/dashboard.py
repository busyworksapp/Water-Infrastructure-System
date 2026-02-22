"""Dashboard API endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.aggregation_service import aggregation_service
from app.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/overview")
def get_system_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        return dashboard_service.get_municipality_dashboard(db, current_user.municipality_id)
    return dashboard_service.get_system_overview(db)


@router.get("/municipality/{municipality_id}")
def get_municipality_dashboard(
    municipality_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin and current_user.municipality_id != municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return dashboard_service.get_municipality_dashboard(db, municipality_id)


@router.get("/sensor-health")
def get_sensor_health(
    municipality_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        municipality_id = current_user.municipality_id
    return dashboard_service.get_sensor_health_summary(db, municipality_id)


@router.get("/activity")
def get_recent_activity(
    municipality_id: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        municipality_id = current_user.municipality_id
    return dashboard_service.get_recent_activity(db, municipality_id, limit)


@router.get("/alerts/summary")
def get_alert_summary(
    municipality_id: Optional[str] = None,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        municipality_id = current_user.municipality_id
    return aggregation_service.alert_summary(db, municipality_id, days)


@router.get("/sensors/{sensor_id}/uptime")
def get_sensor_uptime(
    sensor_id: str,
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return aggregation_service.sensor_uptime(db, sensor_id, hours, current_user)
