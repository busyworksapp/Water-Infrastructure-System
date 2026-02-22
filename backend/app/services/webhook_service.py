"""
Webhook Notification Service
Manages webhook registrations, delivery, retry logic, and security verification
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import hashlib
import hmac
import json
import logging
import asyncio
from enum import Enum

import aiohttp
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class WebhookEvent(str, Enum):
    """Supported webhook events"""
    ALERT_CREATED = "alert.created"
    ALERT_RESOLVED = "alert.resolved"
    INCIDENT_CREATED = "incident.created"
    INCIDENT_RESOLVED = "incident.resolved"
    SENSOR_READING = "sensor.reading"
    ANOMALY_DETECTED = "anomaly.detected"
    DEVICE_OFFLINE = "device.offline"
    DEVICE_ONLINE = "device.online"
    SYSTEM_HEALTH_CHANGED = "system.health_changed"
    MAINTENANCE_ALERT = "maintenance.alert"


class WebhookStatus(str, Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRY = "retry"


class WebhookPayload:
    """Standardized webhook payload"""
    
    def __init__(
        self,
        event: WebhookEvent,
        data: Dict[str, Any],
        timestamp: Optional[datetime] = None,
        source: str = "water_system"
    ):
        self.event = event
        self.data = data
        self.timestamp = timestamp or datetime.utcnow()
        self.source = source
        self.id = self._generate_event_id()

    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        content = f"{self.event}{self.timestamp}{self.data}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for transmission"""
        return {
            "id": self.id,
            "event": self.event,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "data": self.data
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class WebhookSubscription:
    """Webhook subscription model"""
    
    def __init__(
        self,
        id: int,
        url: str,
        events: List[str],
        secret: str,
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        municipality_id: Optional[int] = None
    ):
        self.id = id
        self.url = url
        self.events = events
        self.secret = secret
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.municipality_id = municipality_id
        self.delivery_count = 0
        self.last_delivery = None
        self.failure_count = 0


class WebhookDeliveryLog:
    """Log entry for webhook delivery attempt"""
    
    def __init__(
        self,
        webhook_id: int,
        event: WebhookEvent,
        status: WebhookStatus,
        status_code: Optional[int] = None,
        response: Optional[str] = None,
        error: Optional[str] = None,
        retry_count: int = 0
    ):
        self.webhook_id = webhook_id
        self.event = event
        self.status = status
        self.status_code = status_code
        self.response = response
        self.error = error
        self.retry_count = retry_count
        self.timestamp = datetime.utcnow()


class WebhookService:
    """Service for managing webhook subscriptions and delivery"""

    # Configuration
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 60  # seconds
    TIMEOUT = 10  # seconds
    BATCH_SIZE = 100

    # Storage (in-memory for now, could be replaced with database)
    _subscriptions: Dict[int, WebhookSubscription] = {}
    _delivery_logs: List[WebhookDeliveryLog] = []
    _next_subscription_id = 1

    @classmethod
    async def create_subscription(
        cls,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        municipality_id: Optional[int] = None
    ) -> WebhookSubscription:
        """Create a new webhook subscription"""
        
        # Validate URL
        if not cls._validate_url(url):
            raise ValueError(f"Invalid webhook URL: {url}")

        # Validate events
        valid_events = [e.value for e in WebhookEvent]
        for event in events:
            if event not in valid_events:
                raise ValueError(f"Invalid event: {event}")

        # Generate secret if not provided
        if not secret:
            secret = cls._generate_secret()

        # Create subscription
        subscription = WebhookSubscription(
            id=cls._next_subscription_id,
            url=url,
            events=events,
            secret=secret,
            municipality_id=municipality_id
        )

        cls._subscriptions[subscription.id] = subscription
        cls._next_subscription_id += 1

        logger.info(f"Created webhook subscription {subscription.id} for {url}")
        return subscription

    @classmethod
    async def get_subscription(cls, subscription_id: int) -> Optional[WebhookSubscription]:
        """Get webhook subscription by ID"""
        return cls._subscriptions.get(subscription_id)

    @classmethod
    async def list_subscriptions(
        cls,
        municipality_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> List[WebhookSubscription]:
        """List webhook subscriptions with optional filtering"""
        
        subs = list(cls._subscriptions.values())

        if municipality_id is not None:
            subs = [s for s in subs if s.municipality_id == municipality_id]

        if is_active is not None:
            subs = [s for s in subs if s.is_active == is_active]

        return subs

    @classmethod
    async def update_subscription(
        cls,
        subscription_id: int,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
        is_active: Optional[bool] = None
    ) -> Optional[WebhookSubscription]:
        """Update webhook subscription"""
        
        sub = cls._subscriptions.get(subscription_id)
        if not sub:
            return None

        if url is not None:
            if not cls._validate_url(url):
                raise ValueError(f"Invalid webhook URL: {url}")
            sub.url = url

        if events is not None:
            valid_events = [e.value for e in WebhookEvent]
            for event in events:
                if event not in valid_events:
                    raise ValueError(f"Invalid event: {event}")
            sub.events = events

        if is_active is not None:
            sub.is_active = is_active

        logger.info(f"Updated webhook subscription {subscription_id}")
        return sub

    @classmethod
    async def delete_subscription(cls, subscription_id: int) -> bool:
        """Delete webhook subscription"""
        
        if subscription_id in cls._subscriptions:
            del cls._subscriptions[subscription_id]
            logger.info(f"Deleted webhook subscription {subscription_id}")
            return True
        return False

    @classmethod
    async def deliver_event(cls, payload: WebhookPayload) -> int:
        """Deliver webhook event to all matching subscriptions"""
        
        event_str = payload.event
        delivered_count = 0

        # Get matching subscriptions
        matching_subs = [
            s for s in cls._subscriptions.values()
            if s.is_active and event_str in s.events
        ]

        # Deliver to all matching subscriptions
        tasks = []
        for sub in matching_subs:
            task = cls._deliver_to_subscription(sub, payload)
            tasks.append(task)

        # Execute all deliveries concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            delivered_count = sum(1 for r in results if r is True)

        return delivered_count

    @classmethod
    async def _deliver_to_subscription(
        cls,
        subscription: WebhookSubscription,
        payload: WebhookPayload
    ) -> bool:
        """Deliver webhook to a single subscription"""
        
        for attempt in range(cls.MAX_RETRIES + 1):
            try:
                # Generate signature
                signature = cls._generate_signature(payload.to_json(), subscription.secret)

                # Prepare headers
                headers = {
                    "Content-Type": "application/json",
                    "X-Webhook-Event": payload.event,
                    "X-Webhook-ID": payload.id,
                    "X-Webhook-Signature": signature,
                    "X-Webhook-Timestamp": payload.timestamp.isoformat(),
                }

                # Send request
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        subscription.url,
                        data=payload.to_json(),
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=cls.TIMEOUT)
                    ) as response:
                        # Log delivery
                        log = WebhookDeliveryLog(
                            webhook_id=subscription.id,
                            event=payload.event,
                            status=WebhookStatus.DELIVERED if response.status == 200 else WebhookStatus.FAILED,
                            status_code=response.status,
                            response=await response.text(),
                            retry_count=attempt
                        )
                        cls._delivery_logs.append(log)

                        if response.status == 200:
                            subscription.delivery_count += 1
                            subscription.last_delivery = datetime.utcnow()
                            subscription.failure_count = 0
                            logger.info(
                                f"Webhook {subscription.id} delivered successfully (attempt {attempt + 1})"
                            )
                            return True

            except asyncio.TimeoutError:
                error_msg = "Request timeout"
            except aiohttp.ClientError as e:
                error_msg = str(e)
            except Exception as e:
                error_msg = str(e)

            # Retry logic
            if attempt < cls.MAX_RETRIES:
                delay = cls.INITIAL_RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                logger.warning(
                    f"Webhook {subscription.id} delivery failed (attempt {attempt + 1}), "
                    f"retrying in {delay}s: {error_msg}"
                )
                await asyncio.sleep(delay)
            else:
                # Final failure
                subscription.failure_count += 1
                log = WebhookDeliveryLog(
                    webhook_id=subscription.id,
                    event=payload.event,
                    status=WebhookStatus.FAILED,
                    error=error_msg,
                    retry_count=attempt
                )
                cls._delivery_logs.append(log)
                logger.error(
                    f"Webhook {subscription.id} delivery failed after {attempt + 1} attempts: {error_msg}"
                )

        return False

    @classmethod
    async def get_delivery_logs(
        cls,
        subscription_id: Optional[int] = None,
        event: Optional[str] = None,
        status: Optional[str] = None,
        hours: int = 24
    ) -> List[WebhookDeliveryLog]:
        """Get delivery logs with filtering"""
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        logs = [
            log for log in cls._delivery_logs
            if log.timestamp >= cutoff
        ]

        if subscription_id is not None:
            logs = [log for log in logs if log.webhook_id == subscription_id]

        if event is not None:
            logs = [log for log in logs if log.event == event]

        if status is not None:
            logs = [log for log in logs if log.status == status]

        # Return most recent first
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)

    @classmethod
    async def get_webhook_stats(
        cls,
        subscription_id: int
    ) -> Dict[str, Any]:
        """Get statistics for a webhook subscription"""
        
        sub = cls._subscriptions.get(subscription_id)
        if not sub:
            return {}

        logs = [log for log in cls._delivery_logs if log.webhook_id == subscription_id]

        delivered = sum(1 for log in logs if log.status == WebhookStatus.DELIVERED)
        failed = sum(1 for log in logs if log.status == WebhookStatus.FAILED)

        return {
            "subscription_id": subscription_id,
            "url": sub.url,
            "total_deliveries": len(logs),
            "successful": delivered,
            "failed": failed,
            "success_rate": (delivered / len(logs) * 100) if logs else 0,
            "last_delivery": sub.last_delivery.isoformat() if sub.last_delivery else None,
            "failure_count": sub.failure_count,
            "is_active": sub.is_active
        }

    @classmethod
    def _validate_url(cls, url: str) -> bool:
        """Validate webhook URL"""
        if not url:
            return False
        # Basic validation: must start with http/https and be a valid URL-like string
        return url.startswith("http://") or url.startswith("https://")

    @classmethod
    def _generate_secret(cls) -> str:
        """Generate a random secret for webhook"""
        import secrets
        return secrets.token_urlsafe(32)

    @classmethod
    def _generate_signature(cls, payload: str, secret: str) -> str:
        """Generate HMAC signature for payload"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    @classmethod
    async def verify_webhook_signature(
        cls,
        signature: str,
        payload: str,
        secret: str
    ) -> bool:
        """Verify incoming webhook signature (for receiving webhooks)"""
        
        expected_signature = cls._generate_signature(payload, secret)
        return hmac.compare_digest(signature, expected_signature)

    @classmethod
    async def cleanup_old_logs(cls, days: int = 30) -> int:
        """Clean up old delivery logs"""
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        before_count = len(cls._delivery_logs)
        
        cls._delivery_logs = [
            log for log in cls._delivery_logs
            if log.timestamp >= cutoff
        ]
        
        removed = before_count - len(cls._delivery_logs)
        logger.info(f"Cleaned up {removed} old webhook delivery logs")
        return removed


# Global webhook service instance
webhook_service = WebhookService()
