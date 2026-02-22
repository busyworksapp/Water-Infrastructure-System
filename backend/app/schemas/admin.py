"""Pydantic schemas for admin API endpoints"""

from typing import Optional
from pydantic import BaseModel, Field


# ==================== Sensor Type Schemas ====================

class SensorTypeCreate(BaseModel):
    """Schema for creating a sensor type"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    unit: str = Field(..., min_length=1, max_length=20)
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class SensorTypeUpdate(BaseModel):
    """Schema for updating a sensor type"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    unit: Optional[str] = Field(None, min_length=1, max_length=20)
    min_value: Optional[float] = None
    max_value: Optional[float] = None


# ==================== Protocol Schemas ====================

class ProtocolCreate(BaseModel):
    """Schema for creating an IoT protocol"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    port: int = Field(..., ge=1, le=65535)


class ProtocolUpdate(BaseModel):
    """Schema for updating a protocol"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    port: Optional[int] = Field(None, ge=1, le=65535)
    is_active: Optional[bool] = None


# ==================== Pipeline Schemas ====================

class PipelineCreate(BaseModel):
    """Schema for creating a pipeline"""
    name: str = Field(..., min_length=1, max_length=200)
    diameter: float = Field(..., gt=0)
    material: str = Field(..., min_length=1, max_length=50)
    length: float = Field(..., gt=0)
    municipality_id: int = Field(..., gt=0)


class PipelineUpdate(BaseModel):
    """Schema for updating a pipeline"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    diameter: Optional[float] = Field(None, gt=0)
    material: Optional[str] = Field(None, min_length=1, max_length=50)
    length: Optional[float] = Field(None, gt=0)
    status: Optional[str] = None


# ==================== Alert Rule Schemas ====================

class AlertRuleCreate(BaseModel):
    """Schema for creating an alert rule"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    sensor_type: str = Field(..., min_length=1, max_length=50)
    rule_type: str = Field(..., min_length=1, max_length=50)
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    municipality_id: Optional[int] = None


class AlertRuleUpdate(BaseModel):
    """Schema for updating an alert rule"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    is_active: Optional[bool] = None


# ==================== Maintenance Task Schemas ====================

class MaintenanceTaskCreate(BaseModel):
    """Schema for creating a maintenance task"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority: str = Field("medium", min_length=1, max_length=20)


class MaintenanceTaskUpdate(BaseModel):
    """Schema for updating a maintenance task"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = None
    priority: Optional[str] = None


# ==================== Municipality Schemas ====================

class MunicipalityCreate(BaseModel):
    """Schema for creating a municipality"""
    name: str = Field(..., min_length=1, max_length=100)
    location_type: str = Field(..., min_length=1, max_length=50)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    population: Optional[int] = Field(None, ge=0)
    water_usage_annual: Optional[float] = Field(None, ge=0)


class MunicipalityUpdate(BaseModel):
    """Schema for updating a municipality"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    location_type: Optional[str] = Field(None, min_length=1, max_length=50)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    population: Optional[int] = Field(None, ge=0)
    water_usage_annual: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None


# ==================== User Schemas ====================

class UserCreate(BaseModel):
    """Schema for creating a user"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    role: str = Field("operator", min_length=1, max_length=50)
    municipality_id: Optional[int] = None


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[str] = Field(None, min_length=5, max_length=120)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    role: Optional[str] = Field(None, min_length=1, max_length=50)
    is_active: Optional[bool] = None


# ==================== Audit Log Schemas ====================

class AuditLogResponse(BaseModel):
    """Schema for audit log responses"""
    id: int
    user_id: Optional[int]
    action: str
    resource_type: str
    resource_id: Optional[str]
    ip_address: Optional[str]
    status: str
    error_message: Optional[str]
    created_at: str

    class Config:
        from_attributes = True
