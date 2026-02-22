from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from geoalchemy2.shape import to_shape
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.sensor import Sensor, SensorReading, SensorType, SensorStatus, CommunicationProtocol

router = APIRouter(prefix="/sensors", tags=["Sensors"])


def _get_coords(geom):
    if not geom:
        return None
    try:
        shape = to_shape(geom)
        return [shape.x, shape.y]
    except Exception:
        return None


class CreateSensorRequest(BaseModel):
    device_id: str
    name: str
    sensor_type_id: str
    pipeline_id: Optional[str] = None
    municipality_id: str
    protocol: str
    latitude: float
    longitude: float
    firmware_version: Optional[str] = None
    sampling_interval_sec: Optional[float] = 60
    config: Optional[dict] = Field(default_factory=dict)


class UpdateSensorRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    pipeline_id: Optional[str] = None
    firmware_version: Optional[str] = None
    sampling_interval_sec: Optional[float] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None
    config: Optional[dict] = None


@router.get("/")
async def get_sensors(
    municipality_id: Optional[str] = None,
    status: Optional[SensorStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Sensor)

    if not current_user.is_super_admin:
        query = query.filter(Sensor.municipality_id == current_user.municipality_id)
    elif municipality_id:
        query = query.filter(Sensor.municipality_id == municipality_id)

    if status:
        query = query.filter(Sensor.status == status)

    sensors = query.all()

    return [{
        "id": s.id,
        "device_id": s.device_id,
        "name": s.name,
        "status": s.status.value,
        "protocol": s.protocol.value,
        "sensor_type": s.sensor_type.name if s.sensor_type else None,
        "sensor_type_id": s.sensor_type_id,
        "municipality_id": s.municipality_id,
        "pipeline_id": s.pipeline_id,
        "location": {
            "type": "Point",
            "coordinates": _get_coords(s.location)
        },
        "battery_level": s.battery_level,
        "signal_strength": s.signal_strength,
        "last_reading_at": s.last_reading_at.isoformat() if s.last_reading_at else None
    } for s in sensors]


@router.post("/")
async def create_sensor(
    request: CreateSensorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_super_admin and request.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")

    existing = db.query(Sensor).filter(Sensor.device_id == request.device_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device ID already exists")

    sensor_type = db.query(SensorType).filter(SensorType.id == request.sensor_type_id).first()
    if not sensor_type:
        raise HTTPException(status_code=404, detail="Sensor type not found")

    from geoalchemy2.elements import WKTElement
    point_wkt = f"POINT({request.longitude} {request.latitude})"

    sensor = Sensor(
        device_id=request.device_id,
        name=request.name,
        sensor_type_id=request.sensor_type_id,
        pipeline_id=request.pipeline_id,
        municipality_id=request.municipality_id,
        protocol=CommunicationProtocol(request.protocol.lower()),
        location=WKTElement(point_wkt, srid=4326),
        firmware_version=request.firmware_version,
        sampling_interval_sec=request.sampling_interval_sec,
        config=request.config or {},
        status=SensorStatus.ACTIVE,
        installation_date=datetime.utcnow()
    )

    db.add(sensor)
    db.commit()
    db.refresh(sensor)

    return {
        "id": sensor.id,
        "device_id": sensor.device_id,
        "name": sensor.name,
        "status": sensor.status.value
    }


@router.get("/types")
async def get_sensor_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    types = db.query(SensorType).filter(SensorType.is_active == True).all()
    return [{
        "id": t.id,
        "name": t.name,
        "code": t.code,
        "unit": t.unit,
        "description": t.description,
        "threshold_config": t.threshold_config
    } for t in types]


@router.get("/{sensor_id}")
async def get_sensor(
    sensor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()

    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    if not current_user.is_super_admin and sensor.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": sensor.id,
        "device_id": sensor.device_id,
        "name": sensor.name,
        "status": sensor.status.value,
        "protocol": sensor.protocol.value,
        "sensor_type": {
            "id": sensor.sensor_type.id,
            "name": sensor.sensor_type.name,
            "unit": sensor.sensor_type.unit,
            "threshold_config": sensor.sensor_type.threshold_config
        } if sensor.sensor_type else None,
        "municipality_id": sensor.municipality_id,
        "pipeline_id": sensor.pipeline_id,
        "location": {
            "type": "Point",
            "coordinates": _get_coords(sensor.location)
        },
        "battery_level": sensor.battery_level,
        "signal_strength": sensor.signal_strength,
        "firmware_version": sensor.firmware_version,
        "sampling_interval_sec": sensor.sampling_interval_sec,
        "last_reading_at": sensor.last_reading_at.isoformat() if sensor.last_reading_at else None,
        "installation_date": sensor.installation_date.isoformat() if sensor.installation_date else None,
        "config": sensor.config,
        "extra_data": sensor.extra_data
    }


@router.put("/{sensor_id}")
async def update_sensor(
    sensor_id: str,
    request: UpdateSensorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()

    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    if not current_user.is_super_admin and sensor.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")

    update_data = request.dict(exclude_unset=True)

    if "status" in update_data:
        update_data["status"] = SensorStatus(update_data["status"].lower())

    for field, value in update_data.items():
        setattr(sensor, field, value)

    sensor.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Sensor updated", "id": sensor.id}


@router.delete("/{sensor_id}")
async def delete_sensor(
    sensor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()

    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    if not current_user.is_super_admin and sensor.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(sensor)
    db.commit()

    return {"message": "Sensor deleted"}


@router.get("/{sensor_id}/readings")
async def get_sensor_readings(
    sensor_id: str,
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()

    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    if not current_user.is_super_admin and sensor.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")

    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    readings = db.query(SensorReading).filter(
        SensorReading.sensor_id == sensor_id,
        SensorReading.timestamp >= cutoff_time
    ).order_by(desc(SensorReading.timestamp)).limit(limit).all()

    return [{
        "id": r.id,
        "timestamp": r.timestamp.isoformat(),
        "value": r.value,
        "unit": r.unit,
        "is_anomaly": r.is_anomaly,
        "quality_score": r.quality_score
    } for r in readings]


@router.get("/{sensor_id}/latest")
async def get_latest_reading(
    sensor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()

    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    if not current_user.is_super_admin and sensor.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")

    reading = db.query(SensorReading).filter(
        SensorReading.sensor_id == sensor_id
    ).order_by(desc(SensorReading.timestamp)).first()

    if not reading:
        raise HTTPException(status_code=404, detail="No readings found")

    return {
        "id": reading.id,
        "timestamp": reading.timestamp.isoformat(),
        "value": reading.value,
        "unit": reading.unit,
        "is_anomaly": reading.is_anomaly,
        "quality_score": reading.quality_score
    }

