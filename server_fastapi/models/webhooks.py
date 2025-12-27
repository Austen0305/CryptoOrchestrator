"""
Webhook Models
Webhook management for API integrations
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, JSON, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base, TimestampMixin


class Webhook(Base, TimestampMixin):
    """Webhook definition"""
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Webhook details
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(100), nullable=True)  # For signature verification
    
    # Events
    events = Column(JSON, nullable=False)  # List of event types to subscribe to
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    last_triggered = Column(DateTime, nullable=True)
    
    # Configuration
    config = Column(JSON, nullable=True)  # Additional configuration
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_webhooks_user_active", "user_id", "is_active", "created_at"),
    )


class WebhookDelivery(Base, TimestampMixin):
    """Webhook delivery log"""
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id"), nullable=False, index=True)
    
    # Delivery details
    event_type = Column(String(100), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    
    # Status
    status = Column(String(50), nullable=False, index=True)  # pending, success, failed
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    
    # Timing
    attempted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Relationships
    webhook = relationship("Webhook", foreign_keys=[webhook_id])

    __table_args__ = (
        Index("idx_webhook_deliveries_webhook_status", "webhook_id", "status", "created_at"),
        Index("idx_webhook_deliveries_event_type", "event_type", "created_at"),
    )
