from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from ..core.database import Base


class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True)
    pipeline_id = Column(String(36), ForeignKey("pipelines.id", ondelete="CASCADE"), nullable=True, index=True)
    sensor_id = Column(String(36), ForeignKey("sensors.id", ondelete="CASCADE"), nullable=True, index=True)
    performed_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    maintenance_type = Column(String(100), index=True)
    description = Column(Text, nullable=False)
    work_performed = Column(Text)
    parts_replaced = Column(JSON, default=list)
    cost = Column(Float)
    duration_hours = Column(Float)
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime)
    attachments = Column(JSON, default=list)
    metadata_json = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    incident = relationship("Incident", back_populates="maintenance_logs")
