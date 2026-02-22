"""Advanced analytics API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..services.geospatial_analysis_service import get_geospatial_service
from ..services.event_correlation_engine import correlation_engine
from ..services.predictive_maintenance import PredictiveMaintenanceService

router = APIRouter(prefix="/api/v1/advanced", tags=["advanced-analytics"])


@router.get("/geospatial/leak-detection/{pipeline_id}")
async def detect_pipeline_leaks(
    pipeline_id: str,
    time_window_hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Detect potential leaks along a pipeline using geospatial analysis."""
    geo_service = get_geospatial_service(db)
    result = geo_service.detect_pipeline_leaks(pipeline_id, time_window_hours)
    return result


@router.get("/geospatial/sensors-near")
async def find_sensors_near_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_meters: int = Query(1000, ge=100, le=50000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Find sensors within radius of a location."""
    geo_service = get_geospatial_service(db)
    sensors = geo_service.find_sensors_near_location(latitude, longitude, radius_meters)
    return {"sensors": sensors, "total": len(sensors)}


@router.get("/geospatial/pipeline-health/{pipeline_id}")
async def analyze_pipeline_health(
    pipeline_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive pipeline health analysis."""
    geo_service = get_geospatial_service(db)
    health = geo_service.analyze_pipeline_health(pipeline_id)
    return health


@router.get("/geospatial/pressure-heatmap")
async def get_pressure_heatmap(
    municipality_id: str,
    time_window_minutes: int = Query(60, ge=5, le=1440),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate pressure heatmap data for municipality."""
    if not current_user.is_super_admin and current_user.municipality_id != municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    geo_service = get_geospatial_service(db)
    heatmap = geo_service.create_pressure_heatmap(municipality_id, time_window_minutes)
    return heatmap


@router.get("/geospatial/burst-location/{alert_id}")
async def detect_burst_location(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Triangulate burst location using sensor data."""
    geo_service = get_geospatial_service(db)
    location = geo_service.detect_burst_location(alert_id)
    
    if not location:
        raise HTTPException(status_code=404, detail="Unable to determine burst location")
    
    return location


@router.get("/correlation/active-patterns")
async def get_active_correlations(
    time_window_minutes: int = Query(60, ge=5, le=1440),
    current_user: User = Depends(get_current_user)
):
    """Get currently active event correlation patterns."""
    correlations = correlation_engine.get_active_correlations(time_window_minutes)
    return {"correlations": correlations, "total": len(correlations)}


@router.get("/correlation/event-timeline")
async def get_event_timeline(
    sensor_id: Optional[str] = None,
    minutes: int = Query(60, ge=5, le=1440),
    current_user: User = Depends(get_current_user)
):
    """Get event timeline for correlation analysis."""
    timeline = correlation_engine.get_event_timeline(sensor_id, minutes)
    return {"events": timeline, "total": len(timeline)}


@router.get("/correlation/statistics")
async def get_correlation_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get correlation engine statistics."""
    stats = correlation_engine.get_statistics()
    return stats


@router.get("/predictive/sensor-failure-risk/{sensor_id}")
async def predict_sensor_failure(
    sensor_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Predict sensor failure risk using ML."""
    from ..models.sensor import Sensor
    
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    if not current_user.is_super_admin and current_user.municipality_id != sensor.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    pm_service = PredictiveMaintenanceService()
    risk = pm_service.predict_failure_risk(db, sensor)
    return risk


@router.get("/predictive/maintenance-schedule")
async def get_maintenance_schedule(
    municipality_id: str,
    risk_threshold: str = Query("medium", regex="^(low|medium|high|critical)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recommended maintenance schedule based on predictive analysis."""
    if not current_user.is_super_admin and current_user.municipality_id != municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    from ..models.sensor import Sensor
    
    sensors = db.query(Sensor).filter(
        Sensor.municipality_id == municipality_id,
        Sensor.is_active == True
    ).all()
    
    pm_service = PredictiveMaintenanceService()
    
    risk_levels = {"low": 0.2, "medium": 0.4, "high": 0.6, "critical": 0.8}
    threshold = risk_levels[risk_threshold]
    
    maintenance_needed = []
    for sensor in sensors:
        risk = pm_service.predict_failure_risk(db, sensor)
        if risk.get("score", 0) >= threshold:
            maintenance_needed.append({
                "sensor_id": sensor.id,
                "sensor_name": sensor.name,
                "risk_level": risk["risk_level"],
                "risk_score": risk["score"],
                "recommendation": risk["recommendation"],
                "factors": risk.get("factors", {})
            })
    
    # Sort by risk score descending
    maintenance_needed.sort(key=lambda x: x["risk_score"], reverse=True)
    
    return {
        "municipality_id": municipality_id,
        "risk_threshold": risk_threshold,
        "sensors_requiring_maintenance": len(maintenance_needed),
        "schedule": maintenance_needed
    }


@router.post("/correlation/clear-old-events")
async def clear_old_correlation_events(
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user)
):
    """Clear old events from correlation engine (admin only)."""
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    correlation_engine.clear_old_events(hours)
    return {"status": "success", "message": f"Cleared events older than {hours} hours"}
