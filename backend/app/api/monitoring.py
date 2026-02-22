"""
Monitoring and metrics API endpoints.
Includes health checks, Prometheus metrics, and system status monitoring.
"""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.config import settings
from ..core.security import get_current_user
from ..models.user import User
from ..models.sensor import Sensor, SensorReading
from ..models.alert import Alert
from ..services.monitoring_service import monitoring_service
from ..services.metrics_service import metrics_service
from ..mqtt.client import mqtt_client

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/health")
async def get_health(db: Session = Depends(get_db)):
    """
    Health check endpoint for load balancers.
    No authentication required for monitoring systems.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }
    
    try:
        # Check database connectivity
        db.execute("SELECT 1")
        health_status["database"] = "connected"
        metrics_service.update_system_health("database", True)
    except Exception as e:
        health_status["database"] = "disconnected"
        health_status["status"] = "unhealthy"
        metrics_service.update_system_health("database", False)
    
    return health_status


@router.get("/metrics")
async def get_metrics_prometheus():
    """
    Prometheus metrics endpoint for monitoring systems.
    Returns metrics in Prometheus text format.
    No authentication required.
    """
    if not settings.PROMETHEUS_ENABLED:
        raise HTTPException(status_code=404, detail="Prometheus metrics disabled")
    
    metrics_data = metrics_service.export_metrics()
    return Response(content=metrics_data, media_type="text/plain; version=0.0.4")


@router.get("/status")
async def get_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quick status check"""
    health = monitoring_service.get_system_health(db)
    return {
        "status": health["status"],
        "timestamp": health["timestamp"]
    }


@router.get("/metrics/summary")
async def get_metrics_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = 1
):
    """
    Get summary of key metrics for the last N days.
    
    Parameters:
    - days: Number of days to summarize (default: 1, max: 90)
    """
    if days > 90 or days < 1:
        raise HTTPException(status_code=400, detail="days must be between 1 and 90")
    
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    
    readings_count = db.query(SensorReading).filter(
        SensorReading.created_at >= cutoff_time
    ).count()
    
    anomalies_count = db.query(SensorReading).filter(
        SensorReading.is_anomaly.is_(True),
        SensorReading.created_at >= cutoff_time
    ).count()
    
    alerts_count = db.query(Alert).filter(
        Alert.created_at >= cutoff_time
    ).count()
    
    alerts_by_severity = db.query(
        Alert.severity,
        func.count(Alert.id).label("count")
    ).filter(
        Alert.created_at >= cutoff_time
    ).group_by(Alert.severity).all()
    
    return {
        "period_days": days,
        "readings": readings_count,
        "anomalies": anomalies_count,
        "anomaly_rate": round(anomalies_count / readings_count * 100, 2) if readings_count > 0 else 0,
        "alerts": alerts_count,
        "alerts_by_severity": {
            item[0].value: item[1] for item in alerts_by_severity
        }
    }


@router.get("/system-status")
async def get_system_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive system status.
    """
    try:
        active_sensors = db.query(Sensor).filter(Sensor.is_active.is_(True)).count()
        total_sensors = db.query(Sensor).count()
        
        active_alerts = db.query(Alert).filter(
            Alert.status.in_(["open", "acknowledged"])
        ).count()
        
        recent_readings = db.query(SensorReading).filter(
            SensorReading.created_at >= datetime.utcnow() - timedelta(hours=1)
        ).count()
        
        return {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "sensors": {
                "total": total_sensors,
                "active": active_sensors,
                "inactive": total_sensors - active_sensors
            },
            "alerts": {
                "active": active_alerts
            },
            "performance": {
                "readings_last_hour": recent_readings
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System status unavailable: {str(e)}")


@router.get("/performance")
async def get_performance_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    hours: int = 24
):
    """
    Get performance metrics for the last N hours.
    """
    if hours > 720 or hours < 1:
        raise HTTPException(status_code=400, detail="hours must be between 1 and 720")
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    readings_by_hour = db.query(
        func.date_trunc('hour', SensorReading.created_at).label('hour'),
        func.count(SensorReading.id).label('count')
    ).filter(
        SensorReading.created_at >= cutoff_time
    ).group_by(
        func.date_trunc('hour', SensorReading.created_at)
    ).order_by('hour').all()
    
    anomalies_by_hour = db.query(
        func.date_trunc('hour', SensorReading.created_at).label('hour'),
        func.count(SensorReading.id).label('count')
    ).filter(
        SensorReading.is_anomaly.is_(True),
        SensorReading.created_at >= cutoff_time
    ).group_by(
        func.date_trunc('hour', SensorReading.created_at)
    ).order_by('hour').all()
    
    return {
        "period_hours": hours,
        "readings_by_hour": [
            {"hour": str(r[0]), "count": r[1]} for r in readings_by_hour
        ],
        "anomalies_by_hour": [
            {"hour": str(a[0]), "count": a[1]} for a in anomalies_by_hour
        ]
    }


@router.get("/alerts/statistics")
async def get_alert_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = 7
):
    """
    Get alert statistics for the last N days.
    """
    if days > 90 or days < 1:
        raise HTTPException(status_code=400, detail="days must be between 1 and 90")
    
    cutoff_time = datetime.utcnow() - timedelta(days=days)
    
    total_alerts = db.query(Alert).filter(
        Alert.created_at >= cutoff_time
    ).count()
    
    resolved_alerts = db.query(Alert).filter(
        Alert.created_at >= cutoff_time,
        Alert.status == "resolved"
    ).count()
    
    average_resolution_time = db.query(
        func.avg(Alert.resolved_at - Alert.created_at).label('avg_time')
    ).filter(
        Alert.created_at >= cutoff_time,
        Alert.resolved_at.isnot(None)
    ).scalar()
    
    alerts_by_type = db.query(
        Alert.alert_type,
        func.count(Alert.id).label('count')
    ).filter(
        Alert.created_at >= cutoff_time
    ).group_by(Alert.alert_type).all()
    
    return {
        "period_days": days,
        "total": total_alerts,
        "resolved": resolved_alerts,
        "resolution_rate": round(resolved_alerts / total_alerts * 100, 2) if total_alerts > 0 else 0,
        "average_resolution_time_hours": (
            average_resolution_time.total_seconds() / 3600
            if average_resolution_time else None
        ),
        "by_type": {
            item[0].value: item[1] for item in alerts_by_type
        }
    }


@router.get("/sensors/health")
async def get_sensor_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    municipality_id: Optional[str] = None
):
    """
    Get sensor health metrics.
    """
    query = db.query(Sensor)
    
    if municipality_id:
        query = query.filter(Sensor.municipality_id == municipality_id)
    
    sensors = query.all()
    
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    
    health_data = []
    for sensor in sensors:
        recent_reading = db.query(SensorReading).filter(
            SensorReading.sensor_id == sensor.id,
            SensorReading.created_at >= cutoff_time
        ).order_by(SensorReading.created_at.desc()).first()
        
        if recent_reading:
            is_healthy = (datetime.utcnow() - recent_reading.created_at).total_seconds() < 3600
        else:
            is_healthy = False
        
        health_data.append({
            "sensor_id": sensor.id,
            "name": sensor.name,
            "type": sensor.sensor_type.name if sensor.sensor_type else "unknown",
            "is_active": sensor.is_active,
            "is_healthy": is_healthy,
            "last_reading": recent_reading.created_at.isoformat() if recent_reading else None
        })
    
    return {
        "total": len(sensors),
        "healthy": sum(1 for s in health_data if s["is_healthy"]),
        "unhealthy": sum(1 for s in health_data if not s["is_healthy"]),
        "sensors": health_data
    }


@router.get("/mqtt/status")
async def get_mqtt_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get MQTT broker connection status.
    Requires authentication.
    """
    status = mqtt_client.get_status()
    return {
        "mqtt": status,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/system-connectivity")
async def get_system_connectivity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive system connectivity status including all external services.
    """
    connectivity = {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Database check
    try:
        db.execute("SELECT 1")
        connectivity["services"]["database"] = {"status": "connected"}
    except Exception as e:
        connectivity["services"]["database"] = {"status": "disconnected", "error": str(e)}
    
    # MQTT check
    mqtt_status = mqtt_client.get_status()
    connectivity["services"]["mqtt"] = {
        "status": "connected" if mqtt_status["connected"] else "disconnected",
        "broker": mqtt_status["broker"],
        "reconnect_count": mqtt_status["reconnect_count"]
    }
    
    # Redis check (from metrics service)
    try:
        from ..services.redis_service import redis_service
        redis_healthy = redis_service.is_healthy()
        connectivity["services"]["redis"] = {
            "status": "connected" if redis_healthy else "disconnected"
        }
    except Exception as e:
        connectivity["services"]["redis"] = {"status": "unavailable", "error": str(e)}
    
    # S3 check
    try:
        from ..services.s3_service import s3_service
        connectivity["services"]["s3"] = {
            "status": "configured" if s3_service.enabled else "not configured"
        }
    except Exception as e:
        connectivity["services"]["s3"] = {"status": "error", "error": str(e)}
    
    # Overall system health
    all_critical_connected = all(
        s["status"] == "connected"
        for service, s in connectivity["services"].items()
        if service in ["database", "mqtt"]
    )
    connectivity["overall_status"] = "healthy" if all_critical_connected else "degraded"
    
    return connectivity


