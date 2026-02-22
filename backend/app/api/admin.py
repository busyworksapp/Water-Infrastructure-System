from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from ..core.database import get_db
from ..core.security import get_current_user, get_current_super_admin, get_password_hash
from ..models.user import User, Role, Permission
from ..models.sensor import SensorType
from ..models.system import DynamicRule
from ..models.municipality import Municipality

router = APIRouter(prefix="/admin", tags=["Admin"])


class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    municipality_id: Optional[str] = None
    is_super_admin: bool = False


class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    municipality_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_super_admin: Optional[bool] = None


class CreateSensorTypeRequest(BaseModel):
    name: str
    code: str
    unit: str
    description: Optional[str] = None
    threshold_config: dict = Field(default_factory=dict)


class UpdateSensorTypeRequest(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    threshold_config: Optional[dict] = None
    is_active: Optional[bool] = None


@router.get("/users")
async def list_users(
    municipality_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    query = db.query(User)
    if municipality_id:
        query = query.filter(User.municipality_id == municipality_id)
    users = query.all()

    return [{
        "id": u.id,
        "username": u.username,
        "email": u.email,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "municipality_id": u.municipality_id,
        "is_active": u.is_active,
        "is_super_admin": u.is_super_admin,
        "last_login": u.last_login.isoformat() if u.last_login else None,
        "created_at": u.created_at.isoformat()
    } for u in users]


@router.post("/users")
async def create_user(
    request: CreateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    existing = db.query(User).filter(
        (User.username == request.username) | (User.email == request.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    user = User(
        username=request.username,
        email=request.email,
        password_hash=get_password_hash(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        municipality_id=request.municipality_id,
        is_super_admin=request.is_super_admin,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"id": user.id, "username": user.username}


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "User updated"}


@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "User deactivated"}


@router.post("/users/{user_id}/roles/{role_id}")
async def assign_role_to_user(
    user_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role not in user.roles:
        user.roles.append(role)
        db.commit()

    return {"message": "Role assigned"}


@router.delete("/users/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter(Role.id == role_id).first()
    if role and role in user.roles:
        user.roles.remove(role)
        db.commit()

    return {"message": "Role removed"}


@router.get("/sensor-types")
async def list_sensor_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    types = db.query(SensorType).all()
    return [{
        "id": t.id,
        "name": t.name,
        "code": t.code,
        "unit": t.unit,
        "description": t.description,
        "threshold_config": t.threshold_config,
        "is_active": t.is_active,
        "created_at": t.created_at.isoformat()
    } for t in types]


@router.post("/sensor-types")
async def create_sensor_type(
    request: CreateSensorTypeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    existing = db.query(SensorType).filter(SensorType.code == request.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Sensor type code already exists")

    sensor_type = SensorType(
        name=request.name,
        code=request.code,
        unit=request.unit,
        description=request.description,
        threshold_config=request.threshold_config,
        is_active=True
    )

    db.add(sensor_type)
    db.commit()
    db.refresh(sensor_type)

    return {"id": sensor_type.id, "name": sensor_type.name}


@router.put("/sensor-types/{type_id}")
async def update_sensor_type(
    type_id: str,
    request: UpdateSensorTypeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    sensor_type = db.query(SensorType).filter(SensorType.id == type_id).first()
    if not sensor_type:
        raise HTTPException(status_code=404, detail="Sensor type not found")

    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sensor_type, field, value)

    db.commit()
    return {"message": "Sensor type updated"}


@router.get("/system/stats")
async def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    from ..models.sensor import Sensor, SensorStatus
    from ..models.alert import Alert, AlertStatus

    municipalities = db.query(Municipality).filter(Municipality.is_active == True).count()
    users = db.query(User).filter(User.is_active == True).count()
    sensors = db.query(Sensor).count()
    active_sensors = db.query(Sensor).filter(Sensor.status == SensorStatus.ACTIVE).count()
    open_alerts = db.query(Alert).filter(
        Alert.status.notin_([AlertStatus.RESOLVED, AlertStatus.CLOSED])
    ).count()

    return {
        "municipalities": municipalities,
        "users": users,
        "sensors": {"total": sensors, "active": active_sensors},
        "open_alerts": open_alerts
    }


@router.get("/logs/audit")
async def get_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    from ..models.audit import AuditLog

    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()

    return [{
        "id": log.id,
        "user_id": log.user_id,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "timestamp": log.timestamp.isoformat()
    } for log in logs]

