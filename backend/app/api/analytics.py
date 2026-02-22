from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.sensor import Sensor, SensorReading, SensorStatus
from ..models.alert import Alert, AlertSeverity, AlertStatus
from ..services.predictive_maintenance import PredictiveMaintenanceService

router = APIRouter(prefix="/analytics", tags=["Analytics"])
pm_service = PredictiveMaintenanceService()

@router.get("/dashboard")
async def get_dashboard_analytics(
    municipality_id: Optional[str] = None,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive dashboard analytics"""
    if not current_user.is_super_admin:
        municipality_id = current_user.municipality_id
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Sensor statistics
    sensor_query = db.query(Sensor)
    if municipality_id:
        sensor_query = sensor_query.filter(Sensor.municipality_id == municipality_id)
    
    total_sensors = sensor_query.count()
    active_sensors = sensor_query.filter(Sensor.status == SensorStatus.ACTIVE).count()
    
    # Reading statistics
    reading_query = db.query(SensorReading).filter(SensorReading.timestamp >= cutoff)
    if municipality_id:
        reading_query = reading_query.join(Sensor).filter(Sensor.municipality_id == municipality_id)
    
    total_readings = reading_query.count()
    anomalous_readings = reading_query.filter(SensorReading.is_anomaly == True).count()
    
    # Alert statistics
    alert_query = db.query(Alert).filter(Alert.created_at >= cutoff)
    if municipality_id:
        alert_query = alert_query.filter(Alert.municipality_id == municipality_id)
    
    total_alerts = alert_query.count()
    critical_alerts = alert_query.filter(Alert.severity == AlertSeverity.CRITICAL).count()
    open_alerts = alert_query.filter(Alert.status == AlertStatus.OPEN).count()
    
    return {
        "period_days": days,
        "sensors": {
            "total": total_sensors,
            "active": active_sensors,
            "inactive": total_sensors - active_sensors
        },
        "readings": {
            "total": total_readings,
            "anomalous": anomalous_readings,
            "anomaly_rate": round(anomalous_readings / total_readings * 100, 2) if total_readings > 0 else 0
        },
        "alerts": {
            "total": total_alerts,
            "critical": critical_alerts,
            "open": open_alerts,
            "resolved": total_alerts - open_alerts
        }
    }

@router.get("/trends")
async def get_trends(
    municipality_id: Optional[str] = None,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get time-series trends"""
    if not current_user.is_super_admin:
        municipality_id = current_user.municipality_id
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Daily reading counts
    reading_query = db.query(
        func.date(SensorReading.timestamp).label('date'),
        func.count(SensorReading.id).label('count')
    ).filter(SensorReading.timestamp >= cutoff)
    
    if municipality_id:
        reading_query = reading_query.join(Sensor).filter(Sensor.municipality_id == municipality_id)
    
    daily_readings = reading_query.group_by(func.date(SensorReading.timestamp)).all()
    
    # Daily alert counts
    alert_query = db.query(
        func.date(Alert.created_at).label('date'),
        func.count(Alert.id).label('count')
    ).filter(Alert.created_at >= cutoff)
    
    if municipality_id:
        alert_query = alert_query.filter(Alert.municipality_id == municipality_id)
    
    daily_alerts = alert_query.group_by(func.date(Alert.created_at)).all()
    
    return {
        "readings": [{"date": str(r.date), "count": r.count} for r in daily_readings],
        "alerts": [{"date": str(a.date), "count": a.count} for a in daily_alerts]
    }

@router.get("/sensors/{sensor_id}/health")
async def get_sensor_health(
    sensor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sensor health and predictive maintenance info"""
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    
    if not sensor:
        return {"error": "Sensor not found"}
    
    if not current_user.is_super_admin and sensor.municipality_id != current_user.municipality_id:
        return {"error": "Access denied"}
    
    # Get predictive maintenance analysis
    pm_analysis = pm_service.predict_failure_risk(db, sensor)
    
    # Get recent statistics
    cutoff = datetime.utcnow() - timedelta(days=7)
    recent_readings = db.query(SensorReading).filter(
        SensorReading.sensor_id == sensor_id,
        SensorReading.timestamp >= cutoff
    ).count()
    
    recent_anomalies = db.query(SensorReading).filter(
        SensorReading.sensor_id == sensor_id,
        SensorReading.timestamp >= cutoff,
        SensorReading.is_anomaly == True
    ).count()
    
    return {
        "sensor_id": sensor_id,
        "status": sensor.status.value,
        "battery_level": sensor.battery_level,
        "signal_strength": sensor.signal_strength,
        "last_reading": sensor.last_reading_at.isoformat() if sensor.last_reading_at else None,
        "recent_readings": recent_readings,
        "recent_anomalies": recent_anomalies,
        "predictive_maintenance": pm_analysis
    }

@router.get("/top-alerts")
async def get_top_alerts(
    municipality_id: Optional[str] = None,
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sensors with most alerts"""
    if not current_user.is_super_admin:
        municipality_id = current_user.municipality_id
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(
        Sensor.id,
        Sensor.name,
        Sensor.device_id,
        func.count(Alert.id).label('alert_count')
    ).join(Alert).filter(Alert.created_at >= cutoff)
    
    if municipality_id:
        query = query.filter(Sensor.municipality_id == municipality_id)
    
    results = query.group_by(Sensor.id).order_by(func.count(Alert.id).desc()).limit(limit).all()
    
    return [{
        "sensor_id": r.id,
        "name": r.name,
        "device_id": r.device_id,
        "alert_count": r.alert_count
    } for r in results]

