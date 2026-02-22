import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from ..core.database import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    push_notifications = Column(Boolean, default=True)

    alert_severity_filter = Column(JSON, default=lambda: ["critical", "high", "medium", "low"])
    alert_types_filter = Column(JSON, default=list)

    default_municipality_id = Column(String(36), ForeignKey("municipalities.id", ondelete="SET NULL"), nullable=True)
    dashboard_refresh_interval = Column(Integer, default=30)
    theme = Column(String(20), default="dark")

    default_map_zoom = Column(Integer, default=10)
    default_map_center = Column(JSON, default=lambda: {"lat": -26.2041, "lon": 28.0473})

    user = relationship("User", back_populates="preferences")
    default_municipality = relationship("Municipality")
