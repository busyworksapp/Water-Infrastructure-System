from datetime import datetime
import enum
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from ..core.database import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    municipality_id = Column(
        String(36),
        ForeignKey("municipalities.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    key = Column(String(100), nullable=False, index=True)
    value = Column(JSON, nullable=False)
    description = Column(Text)
    is_public = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    municipality = relationship("Municipality")


class RuleConditionOperator(str, enum.Enum):
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    EQ = "eq"
    NEQ = "neq"
    BETWEEN = "between"
    CHANGE_RATE = "change_rate"
    DELTA = "delta"


class DynamicRule(Base):
    __tablename__ = "dynamic_rules_engine"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    municipality_id = Column(
        String(36),
        ForeignKey("municipalities.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    rule_type = Column(String(100), nullable=False, index=True)
    sensor_type_id = Column(
        String(36),
        ForeignKey("sensor_types.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    conditions = Column(JSON, nullable=False, default=list)
    condition_logic = Column(String(8), nullable=False, default="AND")
    alert_severity = Column(String(50), nullable=False, index=True)
    alert_type = Column(String(100), nullable=False, index=True)
    alert_template = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=100, index=True)
    cooldown_seconds = Column(Integer, default=300)
    metadata_json = Column("metadata", JSON, default=dict)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    municipality = relationship("Municipality")
    sensor_type = relationship("SensorType")


class NotificationChannelType(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    municipality_id = Column(
        String(36),
        ForeignKey("municipalities.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name = Column(String(255), nullable=False)
    channel_type = Column(SQLEnum(NotificationChannelType), nullable=False, index=True)
    config = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    municipality = relationship("Municipality")


class ProtocolType(str, enum.Enum):
    MQTT = "mqtt"
    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    LORAWAN = "lorawan"
    NBIOT = "nbiot"
    GSM = "gsm"


class ProtocolConfiguration(Base):
    __tablename__ = "protocol_configurations"
    __table_args__ = (
        UniqueConstraint("municipality_id", "protocol", name="uq_protocol_scope"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    municipality_id = Column(
        String(36),
        ForeignKey("municipalities.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    protocol = Column(SQLEnum(ProtocolType), nullable=False, index=True)
    is_enabled = Column(Boolean, nullable=False, default=True, index=True)
    settings = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    municipality = relationship("Municipality")


class SchemaExpansion(Base):
    __tablename__ = "schema_expansions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    municipality_id = Column(
        String(36),
        ForeignKey("municipalities.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    table_name = Column(String(128), nullable=False, index=True)
    columns_definition = Column(JSON, nullable=False, default=list)
    status = Column(String(30), nullable=False, default="pending", index=True)
    requested_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    municipality = relationship("Municipality")
