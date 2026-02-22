from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.sensor import SensorReading
from ..models.alert import Incident
from ..services.geospatial_service import geospatial_service

router = APIRouter(prefix="/api/v1/geo", tags=["GIS / Geospatial"])


@router.get("/nearby")
def find_nearby_sensors(
    lat: float,
    lon: float,
    municipality_id: Optional[str] = None,
    radius_km: float = Query(5, ge=0.1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        municipality_id = current_user.municipality_id
    return geospatial_service.find_nearby_sensors(db, lat, lon, radius_km, municipality_id=municipality_id)


@router.get("/pipelines/{pipeline_id}/sensors")
def get_pipeline_sensors(
    pipeline_id: str,
    buffer_meters: float = Query(100, ge=10, le=5000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return geospatial_service.find_sensors_on_pipeline(
        db,
        pipeline_id=pipeline_id,
        buffer_meters=buffer_meters,
        user=current_user,
    )


@router.get("/pipelines/{pipeline_id}/length")
def get_pipeline_length(
    pipeline_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    length = geospatial_service.calculate_pipeline_length(db, pipeline_id, user=current_user)
    return {"pipeline_id": pipeline_id, "length_km": length}


@router.get("/municipalities/{municipality_id}/bounds")
def get_municipality_bounds(
    municipality_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin and current_user.municipality_id != municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")

    bounds = geospatial_service.get_municipality_bounds(db, municipality_id)
    if not bounds:
        raise HTTPException(status_code=404, detail="No sensors found for this municipality")
    return bounds


@router.get("/clusters")
def get_sensor_clusters(
    municipality_id: Optional[str] = None,
    grid_size_meters: int = Query(1000, ge=100, le=50000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        municipality_id = current_user.municipality_id
    return geospatial_service.cluster_sensors(db, municipality_id, grid_size_meters)


@router.get("/sensors/geojson")
def get_sensors_geojson(
    municipality_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        municipality_id = current_user.municipality_id
    return geospatial_service.get_all_sensors_geojson(db, municipality_id)


@router.get("/incidents/{incident_id}/timeline")
def get_incident_timeline(
    incident_id: str,
    hours_before: int = Query(24, ge=1, le=720),
    resolution: int = Query(300, ge=60, le=3600),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get time-based incident playback data.
    Returns historical sensor readings and alert data around the incident time.
    
    Parameters:
    - incident_id: The ID of the incident
    - hours_before: How many hours before incident to include (default: 24, max: 720)
    - resolution: Time resolution in seconds for aggregation (default: 300=5min, max: 3600=1hr)
    
    Returns: GeoJSON FeatureCollection with timeline of readings and alerts
    """
    # Get incident
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Check access permissions
    if not current_user.is_super_admin and current_user.municipality_id != incident.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate time window
    incident_time = incident.created_at
    start_time = incident_time - timedelta(hours=hours_before)
    
    # Get related sensors from pipeline if available
    sensor_ids = []
    if incident.pipeline_id:
        from sqlalchemy.orm import joinedload
        from ..models.sensor import Sensor
        
        pipeline_sensors = db.query(Sensor).filter(
            Sensor.pipeline_id == incident.pipeline_id
        ).all()
        sensor_ids = [s.id for s in pipeline_sensors]
    
    # Build timeline events
    timeline = {
        "type": "FeatureCollection",
        "incident": {
            "id": incident.id,
            "title": incident.title,
            "description": incident.description,
            "created_at": incident.created_at.isoformat(),
            "severity": incident.severity.value,
            "status": incident.status.value
        },
        "metadata": {
            "start_time": start_time.isoformat(),
            "incident_time": incident_time.isoformat(),
            "hours_before": hours_before,
            "resolution_seconds": resolution
        },
        "features": [],
        "timeline_events": []
    }
    
    if sensor_ids:
        # Get sensor readings in the time window
        readings = db.query(SensorReading).filter(
            and_(
                SensorReading.sensor_id.in_(sensor_ids),
                SensorReading.created_at >= start_time,
                SensorReading.created_at <= incident_time + timedelta(hours=1)
            )
        ).order_by(SensorReading.created_at).all()
        
        # Group readings by time interval
        time_buckets = {}
        for reading in readings:
            bucket_time = (reading.created_at.replace(second=0, microsecond=0).timestamp() // resolution) * resolution
            bucket_key = datetime.utcfromtimestamp(bucket_time).isoformat()
            
            if bucket_key not in time_buckets:
                time_buckets[bucket_key] = []
            
            # Create feature for this reading
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [reading.sensor.location.x, reading.sensor.location.y] if reading.sensor.location else [0, 0]
                },
                "properties": {
                    "sensor_id": reading.sensor_id,
                    "sensor_name": reading.sensor.name,
                    "value": float(reading.value),
                    "unit": reading.sensor.unit,
                    "is_anomaly": reading.is_anomaly,
                    "anomaly_score": float(reading.anomaly_score) if reading.anomaly_score else None,
                    "timestamp": reading.created_at.isoformat(),
                    "hours_from_incident": (incident_time - reading.created_at).total_seconds() / 3600
                }
            }
            
            timeline["features"].append(feature)
            time_buckets[bucket_key].append(reading)
        
        # Create timeline events
        for bucket_time in sorted(time_buckets.keys()):
            readings_in_bucket = time_buckets[bucket_time]
            event = {
                "timestamp": bucket_time,
                "reading_count": len(readings_in_bucket),
                "average_value": sum(float(r.value) for r in readings_in_bucket) / len(readings_in_bucket),
                "anomaly_count": sum(1 for r in readings_in_bucket if r.is_anomaly),
                "sensors": list(set(r.sensor_id for r in readings_in_bucket))
            }
            timeline["timeline_events"].append(event)
    
    # Add related alerts
    from ..models.alert import Alert
    related_alerts = db.query(Alert).filter(
        and_(
            Alert.municipality_id == incident.municipality_id,
            Alert.created_at >= start_time,
            Alert.created_at <= incident_time + timedelta(hours=1)
        )
    ).order_by(Alert.created_at).all()
    
    timeline["related_alerts"] = [
        {
            "id": alert.id,
            "type": alert.alert_type.value,
            "severity": alert.severity.value,
            "message": alert.message,
            "timestamp": alert.created_at.isoformat(),
            "hours_from_incident": (incident_time - alert.created_at).total_seconds() / 3600
        }
        for alert in related_alerts
    ]
    
    return timeline
