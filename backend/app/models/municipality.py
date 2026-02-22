from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, JSON, String, Text
from sqlalchemy.orm import relationship

from ..core.database import Base


class Municipality(Base):
    __tablename__ = "municipalities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    region = Column(String(100))
    province = Column(String(100))
    contact_person = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    address = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship("User", back_populates="municipality", cascade="all, delete-orphan")
    pipelines = relationship("Pipeline", back_populates="municipality", cascade="all, delete-orphan")
    sensors = relationship("Sensor", back_populates="municipality", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="municipality", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="municipality", cascade="all, delete-orphan")
