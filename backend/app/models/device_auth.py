from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ..core.database import Base

class DeviceAuthentication(Base):
    __tablename__ = "device_authentication"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sensor_id = Column(String(36), ForeignKey('sensors.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    device_id = Column(String(100), nullable=False, unique=True, index=True)
    api_key = Column(String(255), unique=True, index=True)
    certificate_fingerprint = Column(String(255))
    certificate_pem = Column(Text)
    mqtt_username = Column(String(100))
    mqtt_password_hash = Column(String(255))
    is_active = Column(Boolean, default=True, index=True)
    last_authenticated = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
