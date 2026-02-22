from datetime import datetime
import enum
import uuid

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from ..core.database import Base


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"


class AlertType(str, enum.Enum):
    LEAK = "leak"
    BURST = "burst"
    PRESSURE_ANOMALY = "pressure_anomaly"
    FLOW_IRREGULARITY = "flow_irregularity"
    INFRASTRUCTURE_DAMAGE = "infrastructure_damage"
    SENSOR_FAULT = "sensor_fault"
    COMMUNICATION_LOSS = "communication_loss"
    CUSTOM = "custom"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    municipality_id = Column(
        String(36),
        ForeignKey("municipalities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sensor_id = Column(String(36), ForeignKey("sensors.id", ondelete="CASCADE"), nullable=True, index=True)
    pipeline_id = Column(String(36), ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=True, index=True)
    alert_type = Column(SQLEnum(AlertType), nullable=False, index=True)
    severity = Column(SQLEnum(AlertSeverity), nullable=False, index=True)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.OPEN, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    location = Column(Geometry("POINT", srid=4326))
    rule_id = Column(
        String(36),
        ForeignKey("dynamic_rules_engine.id", ondelete="SET NULL"),
        nullable=True,
    )
    triggered_value = Column(JSON, default=dict)
    threshold_value = Column(JSON, default=dict)
    acknowledged_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    acknowledged_at = Column(DateTime)
    resolved_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    resolved_at = Column(DateTime)
    resolution_notes = Column(Text)
    metadata_json = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    municipality = relationship("Municipality", back_populates="alerts")
    sensor = relationship("Sensor", back_populates="alerts")
    incidents = relationship("Incident", back_populates="alert", cascade="all, delete-orphan")


class IncidentStatus(str, enum.Enum):
    REPORTED = "reported"
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    REPAIRING = "repairing"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(36), ForeignKey("alerts.id", ondelete="CASCADE"), nullable=True, index=True)
    municipality_id = Column(
        String(36),
        ForeignKey("municipalities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pipeline_id = Column(String(36), ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    incident_type = Column(String(100), index=True)
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.REPORTED, index=True)
    severity = Column(SQLEnum(AlertSeverity), nullable=False, index=True)
    location = Column(Geometry("POINT", srid=4326))
    reported_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    assigned_to = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    estimated_impact = Column(Text)
    resolution_notes = Column(Text)
    attachments = Column(JSON, default=list)
    metadata_json = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)

    alert = relationship("Alert", back_populates="incidents")
    maintenance_logs = relationship("MaintenanceLog", back_populates="incident", cascade="all, delete-orphan")
