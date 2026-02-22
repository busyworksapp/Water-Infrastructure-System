from datetime import datetime
import enum
import uuid

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..core.database import Base


class SensorStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    FAULTY = "faulty"


class CommunicationProtocol(str, enum.Enum):
    MQTT = "mqtt"
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    LORAWAN = "lorawan"
    NBIOT = "nbiot"
    GSM = "gsm"


class SensorType(Base):
    __tablename__ = "sensor_types"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text)
    unit = Column(String(50))
    data_schema = Column(JSON, default=dict)
    threshold_config = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sensors = relationship("Sensor", back_populates="sensor_type")


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    municipality_id = Column(
        String(36),
        ForeignKey("municipalities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pipeline_id = Column(
        String(36),
        ForeignKey("pipelines.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    sensor_type_id = Column(
        String(36),
        ForeignKey("sensor_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    device_id = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    status = Column(SQLEnum(SensorStatus), default=SensorStatus.ACTIVE, index=True)
    protocol = Column(SQLEnum(CommunicationProtocol), nullable=False, index=True)
    firmware_version = Column(String(50))
    battery_level = Column(Float)
    signal_strength = Column(Float)
    sampling_interval_sec = Column(Float, default=60)
    last_reading_at = Column(DateTime, index=True)
    last_maintenance_at = Column(DateTime)
    installation_date = Column(DateTime)
    config = Column(JSON, default=dict)
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    municipality = relationship("Municipality", back_populates="sensors")
    pipeline = relationship("Pipeline", back_populates="sensors")
    sensor_type = relationship("SensorType", back_populates="sensors")
    readings = relationship("SensorReading", back_populates="sensor", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="sensor", cascade="all, delete-orphan")


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    __table_args__ = (
        Index("idx_sensor_timestamp", "sensor_id", "timestamp"),
        Index("idx_timestamp", "timestamp"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sensor_id = Column(String(36), ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    raw_data = Column(JSON, default=dict)
    quality_score = Column(Float)
    is_anomaly = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    sensor = relationship("Sensor", back_populates="readings")
