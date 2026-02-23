"""Device registration and authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..services.device_auth_service import device_auth_service
from ..models.device_auth import DeviceAuthentication

router = APIRouter(prefix="/api/v1/devices", tags=["Device Management"])


class DeviceRegistrationRequest(BaseModel):
    """Device registration request"""
    sensor_id: str = Field(..., description="Associated sensor ID")
    device_id: str = Field(..., description="Device identifier")
    authentication_method: str = Field(
        default="api_key",
        description="Authentication method: api_key, certificate, mqtt"
    )
    certificate_pem: Optional[str] = Field(None, description="PEM-encoded certificate for cert auth")
    mqtt_password: Optional[str] = Field(None, description="MQTT password for mqtt auth")


class DeviceAuthenticationRequest(BaseModel):
    """Device authentication request"""
    device_id: str = Field(..., description="Device identifier")
    authentication_type: str = Field(
        ...,
        description="Authentication type: api_key, certificate_fingerprint, mqtt_password"
    )
    credential: str = Field(..., description="The credential to verify")


class CertificateGenerationRequest(BaseModel):
    """Certificate generation request"""
    device_id: str = Field(..., description="Device identifier")
    common_name: str = Field(..., description="Common name for certificate")
    validity_days: int = Field(default=365, description="Certificate validity in days")


@router.post("/register")
async def register_device(
    request: DeviceRegistrationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register a new device with authentication credentials.
    
    Requires admin role.
    """
    if not (current_user.is_super_admin or current_user.is_municipality_admin):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    success, message, credentials = device_auth_service.register_device(
        db=db,
        sensor_id=request.sensor_id,
        device_id=request.device_id,
        authentication_method=request.authentication_method,
        certificate_pem=request.certificate_pem,
        mqtt_password=request.mqtt_password,
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "device_id": request.device_id,
        "authentication_method": request.authentication_method,
        "credentials": credentials,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/authenticate")
async def authenticate_device(
    request: DeviceAuthenticationRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate a device with its credentials.
    
    No user authentication required - this endpoint is for IoT devices.
    """
    success, message, sensor_id = device_auth_service.authenticate_device(
        db=db,
        device_id=request.device_id,
        authentication_type=request.authentication_type,
        credential=request.credential,
    )
    
    if not success:
        raise HTTPException(status_code=401, detail=message)
    
    return {
        "success": True,
        "message": message,
        "device_id": request.device_id,
        "sensor_id": sensor_id,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/{device_id}")
async def get_device_info(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get device information and status."""
    device_info = device_auth_service.get_device_info(db, device_id)
    
    if not device_info:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return device_info


@router.get("/")
async def list_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all registered devices."""
    query = db.query(DeviceAuthentication)
    
    if not current_user.is_super_admin:
        from ..models.sensor import Sensor
        sensor_ids = [
            s.id for s in db.query(Sensor)
            .filter(Sensor.municipality_id == current_user.municipality_id).all()
        ]
        query = query.filter(DeviceAuthentication.sensor_id.in_(sensor_ids))
    
    devices = query.all()
    return [
        device_auth_service.get_device_info(db, d.device_id)
        for d in devices
    ]


@router.post("/{device_id}/refresh-api-key")
async def refresh_api_key(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Refresh API key for a device."""
    if not (current_user.is_super_admin or current_user.is_municipality_admin):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    success, message, new_api_key = device_auth_service.refresh_api_key(db, device_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "device_id": device_id,
        "new_api_key": new_api_key,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/{device_id}/deactivate")
async def deactivate_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate a device."""
    if not (current_user.is_super_admin or current_user.is_municipality_admin):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    success, message = device_auth_service.deactivate_device(db, device_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "device_id": device_id,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/{device_id}/reactivate")
async def reactivate_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reactivate a device."""
    if not (current_user.is_super_admin or current_user.is_municipality_admin):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    success, message = device_auth_service.reactivate_device(db, device_id)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "device_id": device_id,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/certificates/generate")
async def generate_certificate(
    request: CertificateGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a self-signed certificate for a device."""
    if not (current_user.is_super_admin or current_user.is_municipality_admin):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    success, message, cert_data = device_auth_service.generate_certificate(
        device_id=request.device_id,
        common_name=request.common_name,
        validity_days=request.validity_days
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        "success": True,
        "message": message,
        "device_id": request.device_id,
        "certificate_pem": cert_data["certificate_pem"],
        "private_key_pem": cert_data["private_key_pem"],
        "certificate_fingerprint": cert_data["certificate_fingerprint"],
        "validity_days": cert_data["validity_days"],
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/check/{device_id}")
async def check_device_heartbeat(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check device heartbeat status."""
    is_healthy = device_auth_service.check_device_heartbeat(db, device_id)
    
    return {
        "device_id": device_id,
        "is_healthy": is_healthy,
        "timestamp": datetime.utcnow().isoformat()
    }

