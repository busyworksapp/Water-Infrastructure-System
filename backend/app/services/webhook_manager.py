"""Webhook management for external integrations."""
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import httpx
import hmac
import hashlib
import json
import logging

from ..models.webhook import Webhook, WebhookDelivery

logger = logging.getLogger(__name__)

class WebhookManager:
    """Manage webhook subscriptions and deliveries."""
    
    def __init__(self, db: Session):
        self.db = db
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def trigger_webhook(
        self,
        event_type: str,
        payload: Dict,
        municipality_id: str
    ):
        """Trigger webhooks for specific event type."""
        webhooks = self.db.query(Webhook).filter(
            Webhook.municipality_id == municipality_id,
            Webhook.is_active == True,
            Webhook.events.contains([event_type])
        ).all()
        
        for webhook in webhooks:
            await self._deliver_webhook(webhook, event_type, payload)
    
    async def _deliver_webhook(
        self,
        webhook: Webhook,
        event_type: str,
        payload: Dict
    ):
        """Deliver webhook to endpoint."""
        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=event_type,
            payload=payload,
            status="pending"
        )
        self.db.add(delivery)
        self.db.commit()
        
        try:
            # Prepare payload
            full_payload = {
                "event": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": payload
            }
            
            # Generate signature
            signature = self._generate_signature(
                json.dumps(full_payload),
                webhook.secret
            )
            
            # Send request
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
                "X-Webhook-Event": event_type
            }
            
            response = await self.client.post(
                webhook.url,
                json=full_payload,
                headers=headers
            )
            
            # Update delivery status
            delivery.status = "success" if response.status_code < 400 else "failed"
            delivery.response_code = response.status_code
            delivery.response_body = response.text[:1000]  # Limit size
            delivery.delivered_at = datetime.utcnow()
            
            logger.info(f"Webhook delivered: {webhook.url} - {delivery.status}")
            
        except Exception as e:
            delivery.status = "failed"
            delivery.error_message = str(e)[:500]
            logger.error(f"Webhook delivery failed: {webhook.url} - {e}")
        
        finally:
            self.db.commit()
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def get_webhook_stats(self, webhook_id: str) -> Dict:
        """Get delivery statistics for webhook."""
        total = self.db.query(WebhookDelivery).filter(
            WebhookDelivery.webhook_id == webhook_id
        ).count()
        
        successful = self.db.query(WebhookDelivery).filter(
            WebhookDelivery.webhook_id == webhook_id,
            WebhookDelivery.status == "success"
        ).count()
        
        failed = self.db.query(WebhookDelivery).filter(
            WebhookDelivery.webhook_id == webhook_id,
            WebhookDelivery.status == "failed"
        ).count()
        
        return {
            "webhook_id": webhook_id,
            "total_deliveries": total,
            "successful": successful,
            "failed": failed,
            "success_rate": round((successful / total * 100), 2) if total > 0 else 0
        }
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
