from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from ..core.database import get_db
from ..core.security import get_current_user, get_current_super_admin
from ..models.user import User
from ..models.municipality import Municipality

router = APIRouter(prefix="/municipalities", tags=["Municipalities"])


class CreateMunicipalityRequest(BaseModel):
    name: str
    code: str
    region: Optional[str] = None
    province: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    settings: Optional[dict] = Field(default_factory=dict)


class UpdateMunicipalityRequest(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    province: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[dict] = None


@router.get("/")
async def get_municipalities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.is_super_admin:
        municipalities = db.query(Municipality).all()
    else:
        municipalities = db.query(Municipality).filter(
            Municipality.id == current_user.municipality_id
        ).all()

    return [{
        "id": m.id,
        "name": m.name,
        "code": m.code,
        "region": m.region,
        "province": m.province,
        "is_active": m.is_active,
        "contact_person": m.contact_person,
        "contact_email": m.contact_email,
        "contact_phone": m.contact_phone,
        "created_at": m.created_at.isoformat()
    } for m in municipalities]


@router.post("/")
async def create_municipality(
    request: CreateMunicipalityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    existing = db.query(Municipality).filter(
        (Municipality.name == request.name) | (Municipality.code == request.code)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Municipality name or code already exists")

    municipality = Municipality(
        name=request.name,
        code=request.code,
        region=request.region,
        province=request.province,
        contact_person=request.contact_person,
        contact_email=request.contact_email,
        contact_phone=request.contact_phone,
        address=request.address,
        settings=request.settings or {},
        is_active=True
    )

    db.add(municipality)
    db.commit()
    db.refresh(municipality)

    return {"id": municipality.id, "name": municipality.name, "code": municipality.code}


@router.get("/{municipality_id}")
async def get_municipality(
    municipality_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_super_admin and current_user.municipality_id != municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")

    municipality = db.query(Municipality).filter(Municipality.id == municipality_id).first()
    if not municipality:
        raise HTTPException(status_code=404, detail="Municipality not found")

    from ..models.sensor import Sensor, SensorStatus
    from ..models.alert import Alert, AlertStatus

    total_sensors = db.query(Sensor).filter(Sensor.municipality_id == municipality_id).count()
    active_sensors = db.query(Sensor).filter(
        Sensor.municipality_id == municipality_id,
        Sensor.status == SensorStatus.ACTIVE
    ).count()
    open_alerts = db.query(Alert).filter(
        Alert.municipality_id == municipality_id,
        Alert.status == AlertStatus.OPEN
    ).count()

    return {
        "id": municipality.id,
        "name": municipality.name,
        "code": municipality.code,
        "region": municipality.region,
        "province": municipality.province,
        "contact_person": municipality.contact_person,
        "contact_email": municipality.contact_email,
        "contact_phone": municipality.contact_phone,
        "address": municipality.address,
        "is_active": municipality.is_active,
        "settings": municipality.settings,
        "stats": {
            "total_sensors": total_sensors,
            "active_sensors": active_sensors,
            "open_alerts": open_alerts
        },
        "created_at": municipality.created_at.isoformat(),
        "updated_at": municipality.updated_at.isoformat()
    }


@router.put("/{municipality_id}")
async def update_municipality(
    municipality_id: str,
    request: UpdateMunicipalityRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    municipality = db.query(Municipality).filter(Municipality.id == municipality_id).first()
    if not municipality:
        raise HTTPException(status_code=404, detail="Municipality not found")

    for field, value in request.dict(exclude_unset=True).items():
        setattr(municipality, field, value)

    municipality.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Municipality updated", "id": municipality_id}


@router.delete("/{municipality_id}")
async def delete_municipality(
    municipality_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    municipality = db.query(Municipality).filter(Municipality.id == municipality_id).first()
    if not municipality:
        raise HTTPException(status_code=404, detail="Municipality not found")

    municipality.is_active = False
    municipality.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Municipality deactivated"}


@router.get("/{municipality_id}/stats")
async def get_municipality_stats(
    municipality_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_super_admin and current_user.municipality_id != municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")

    from ..models.sensor import Sensor, SensorStatus
    from ..models.alert import Alert, AlertStatus, AlertSeverity
    from ..models.pipeline import Pipeline

    total_sensors = db.query(Sensor).filter(Sensor.municipality_id == municipality_id).count()
    active_sensors = db.query(Sensor).filter(
        Sensor.municipality_id == municipality_id,
        Sensor.status == SensorStatus.ACTIVE
    ).count()
    total_pipelines = db.query(Pipeline).filter(Pipeline.municipality_id == municipality_id).count()
    open_alerts = db.query(Alert).filter(
        Alert.municipality_id == municipality_id,
        Alert.status == AlertStatus.OPEN
    ).count()
    critical_alerts = db.query(Alert).filter(
        Alert.municipality_id == municipality_id,
        Alert.status == AlertStatus.OPEN,
        Alert.severity == AlertSeverity.CRITICAL
    ).count()

    return {
        "municipality_id": municipality_id,
        "total_sensors": total_sensors,
        "active_sensors": active_sensors,
        "total_pipelines": total_pipelines,
        "open_alerts": open_alerts,
        "critical_alerts": critical_alerts
    }

