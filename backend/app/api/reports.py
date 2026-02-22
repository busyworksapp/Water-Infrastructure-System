from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.alert import AlertStatus
from ..models.sensor import SensorStatus
from ..services.export_service import export_service

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/sensors/{sensor_id}/export")
async def export_sensor_data(
    sensor_id: str,
    days: int = Query(7, ge=1, le=90),
    format: str = Query("csv", pattern="^(csv|json)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export sensor readings"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    if format == "csv":
        csv_data = export_service.export_sensor_readings_csv(db, sensor_id, start_date, end_date)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=sensor_{sensor_id}_readings.csv"}
        )
    
    return {"error": "Format not supported"}

@router.get("/alerts/export")
async def export_alerts(
    municipality_id: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    format: str = Query("csv", pattern="^(csv|json)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export alerts"""
    if not current_user.is_super_admin:
        municipality_id = current_user.municipality_id
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    if format == "csv":
        csv_data = export_service.export_alerts_csv(db, municipality_id, start_date, end_date)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=alerts_{municipality_id}.csv"}
        )
    
    return {"error": "Format not supported"}

@router.get("/municipality/{municipality_id}")
async def get_municipality_report(
    municipality_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive municipality report"""
    if not current_user.is_super_admin and current_user.municipality_id != municipality_id:
        return {"error": "Access denied"}
    
    return export_service.export_municipality_report_json(db, municipality_id, days)

@router.get("/system/summary")
async def get_system_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get system-wide summary (super admin only)"""
    if not current_user.is_super_admin:
        return {"error": "Super admin access required"}
    
    from ..models.municipality import Municipality
    from ..models.sensor import Sensor
    from ..models.alert import Alert
    
    municipalities = db.query(Municipality).filter(Municipality.is_active == True).count()
    total_sensors = db.query(Sensor).count()
    active_sensors = db.query(Sensor).filter(Sensor.status == SensorStatus.ACTIVE).count()
    
    cutoff = datetime.utcnow() - timedelta(days=7)
    recent_alerts = db.query(Alert).filter(Alert.created_at >= cutoff).count()
    open_alerts = db.query(Alert).filter(Alert.status == AlertStatus.OPEN).count()
    
    return {
        "system": {
            "municipalities": municipalities,
            "total_sensors": total_sensors,
            "active_sensors": active_sensors,
            "sensor_uptime": round(active_sensors / total_sensors * 100, 2) if total_sensors > 0 else 0
        },
        "alerts_last_7_days": recent_alerts,
        "open_alerts": open_alerts,
        "generated_at": datetime.utcnow().isoformat()
    }

