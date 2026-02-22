"""Webhook models for external integrations."""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ..core.database import Base

class Webhook(Base):
    """Webhook subscription model."""
    __tablename__ = "webhooks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    municipality_id = Column(String(36), ForeignKey("municipalities.id"), nullable=False)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(100), nullable=False)
    events = Column(JSON, nullable=False)  # List of event types
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    municipality = relationship("Municipality", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")

class WebhookDelivery(Base):
    """Webhook delivery log model."""
    __tablename__ = "webhook_deliveries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    webhook_id = Column(String(36), ForeignKey("webhooks.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False)  # pending, success, failed
    response_code = Column(Integer)
    response_body = Column(Text)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime)
    
    # Relationships
    webhook = relationship("Webhook", back_populates="deliveries")
