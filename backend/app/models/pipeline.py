from datetime import datetime
import enum
import uuid

from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Enum as SQLEnum, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from ..core.database import Base


class PipelineStatus(str, enum.Enum):
    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    DAMAGED = "damaged"
    INACTIVE = "inactive"


class PipelineMaterial(str, enum.Enum):
    PVC = "pvc"
    STEEL = "steel"
    CONCRETE = "concrete"
    HDPE = "hdpe"
    CAST_IRON = "cast_iron"
    DUCTILE_IRON = "ductile_iron"


class Pipeline(Base):
    __tablename__ = "pipelines"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    municipality_id = Column(
        String(36),
        ForeignKey("municipalities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(100), unique=True, index=True)
    geometry = Column(Geometry("LINESTRING", srid=4326), nullable=False)
    length_km = Column(Float)
    diameter_mm = Column(Float)
    material = Column(SQLEnum(PipelineMaterial))
    installation_date = Column(DateTime)
    status = Column(SQLEnum(PipelineStatus), default=PipelineStatus.OPERATIONAL, index=True)
    max_pressure_bar = Column(Float)
    max_flow_rate = Column(Float)
    description = Column(Text)
    extra_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    municipality = relationship("Municipality", back_populates="pipelines")
    sensors = relationship("Sensor", back_populates="pipeline", cascade="all, delete-orphan")
