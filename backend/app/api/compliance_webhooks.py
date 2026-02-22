"""
Compliance and Webhook API Endpoints
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, HttpUrl

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.compliance_service import (
    compliance_service,
    ComplianceStandard,
    ComplianceMetric,
    ComplianceStatus
)
from app.services.webhook_service import (
    webhook_service,
    WebhookEvent,
    WebhookPayload
)

router = APIRouter(prefix="/api/v1", tags=["Compliance & Webhooks"])


# ============================================================================
# COMPLIANCE ENDPOINTS
# ============================================================================

class ComplianceMetricRequest(BaseModel):
    """Request to check compliance for a metric"""
    metric: str
    value: float
    standard: str = "WHO"


class ComplianceMetricResponse(BaseModel):
    """Response for compliance check"""
    metric: str
    value: float
    threshold_min: float
    threshold_max: float
    status: str
    notes: Optional[str] = None


@router.post("/compliance/check")
async def check_compliance(
    request: ComplianceMetricRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Check if a metric value complies with a standard
    
    - **metric**: Metric name (pH, turbidity, bacteria, etc.)
    - **value**: Current metric value
    - **standard**: Compliance standard (WHO, EPA, EU, LOCAL)
    """
    
    try:
        metric = ComplianceMetric[request.metric.upper()]
        standard = ComplianceStandard[request.standard.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid metric or standard")

    result = compliance_service.check_compliance(
        metric=metric,
        value=request.value,
        standard=standard
    )

    return ComplianceMetricResponse(
        metric=result.metric,
        value=result.value,
        threshold_min=result.threshold_min,
        threshold_max=result.threshold_max,
        status=result.status,
        notes=result.notes
    )


@router.get("/compliance/municipality/{municipality_id}")
async def get_compliance_report(
    municipality_id: int,
    standard: str = Query("WHO"),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user)
):
    """
    Get compliance report for a municipality
    
    - **municipality_id**: Municipality to report on
    - **standard**: Compliance standard (WHO, EPA, EU)
    - **days**: Historical period
    """
    
    # Check permissions
    if not current_user.is_super_admin and current_user.municipality_id != municipality_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        std = ComplianceStandard[standard.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid standard")

    report = compliance_service.generate_compliance_report(
        municipality_id=municipality_id,
        standard=std,
        days=days
    )

    return report


@router.get("/compliance/audit-trail/{municipality_id}")
async def get_compliance_audit_trail(
    municipality_id: int,
    days: int = Query(90, ge=1, le=365),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit trail of compliance issues for a municipality
    
    - **municipality_id**: Municipality to audit
    - **days**: Historical period
    """
    
    # Check permissions
    if not current_user.is_super_admin and current_user.municipality_id != municipality_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    trail = compliance_service.get_audit_trail(
        municipality_id=municipality_id,
        days=days
    )

    return {"audit_trail": trail}


@router.post("/compliance/action-plan/{municipality_id}")
async def create_compliance_action_plan(
    municipality_id: int,
    metrics: List[str],
    current_user: User = Depends(get_current_user)
):
    """
    Create action plan for non-compliant metrics
    
    - **municipality_id**: Municipality to create plan for
    - **metrics**: List of non-compliant metric names
    """
    
    # Check permissions
    if not current_user.is_super_admin and current_user.municipality_id != municipality_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        metric_enums = [ComplianceMetric[m.upper()] for m in metrics]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid metric name")

    plan = compliance_service.create_compliance_action_plan(
        municipality_id=municipality_id,
        non_compliant_metrics=metric_enums
    )

    return plan


# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

class WebhookSubscriptionRequest(BaseModel):
    """Request to create/update webhook subscription"""
    url: HttpUrl
    events: List[str]
    secret: Optional[str] = None


class WebhookSubscriptionResponse(BaseModel):
    """Response for webhook subscription"""
    id: int
    url: str
    events: List[str]
    is_active: bool
    created_at: datetime
    delivery_count: int
    failure_count: int


@router.post("/webhooks/subscribe")
async def create_webhook_subscription(
    request: WebhookSubscriptionRequest,
    municipality_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new webhook subscription
    
    - **url**: Webhook URL to receive events
    - **events**: List of events to subscribe to
    - **secret**: Optional secret for signature verification
    """
    
    # Non-admin users can only create for their own municipality
    if not current_user.is_super_admin:
        municipality_id = current_user.municipality_id

    try:
        subscription = await webhook_service.create_subscription(
            url=str(request.url),
            events=request.events,
            secret=request.secret,
            municipality_id=municipality_id
        )

        return WebhookSubscriptionResponse(
            id=subscription.id,
            url=subscription.url,
            events=subscription.events,
            is_active=subscription.is_active,
            created_at=subscription.created_at,
            delivery_count=subscription.delivery_count,
            failure_count=subscription.failure_count
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/webhooks/subscriptions")
async def list_webhook_subscriptions(
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    """
    List webhook subscriptions
    
    - **is_active**: Filter by active status (optional)
    """
    
    municipality_id = None if current_user.is_super_admin else current_user.municipality_id

    subscriptions = await webhook_service.list_subscriptions(
        municipality_id=municipality_id,
        is_active=is_active
    )

    return [
        WebhookSubscriptionResponse(
            id=s.id,
            url=s.url,
            events=s.events,
            is_active=s.is_active,
            created_at=s.created_at,
            delivery_count=s.delivery_count,
            failure_count=s.failure_count
        )
        for s in subscriptions
    ]


@router.get("/webhooks/subscriptions/{subscription_id}")
async def get_webhook_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get details of a webhook subscription"""
    
    subscription = await webhook_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Check permissions
    if not current_user.is_super_admin and subscription.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    return WebhookSubscriptionResponse(
        id=subscription.id,
        url=subscription.url,
        events=subscription.events,
        is_active=subscription.is_active,
        created_at=subscription.created_at,
        delivery_count=subscription.delivery_count,
        failure_count=subscription.failure_count
    )


@router.put("/webhooks/subscriptions/{subscription_id}")
async def update_webhook_subscription(
    subscription_id: int,
    request: WebhookSubscriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """Update a webhook subscription"""
    
    subscription = await webhook_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Check permissions
    if not current_user.is_super_admin and subscription.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        updated = await webhook_service.update_subscription(
            subscription_id=subscription_id,
            url=str(request.url),
            events=request.events
        )

        return WebhookSubscriptionResponse(
            id=updated.id,
            url=updated.url,
            events=updated.events,
            is_active=updated.is_active,
            created_at=updated.created_at,
            delivery_count=updated.delivery_count,
            failure_count=updated.failure_count
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/webhooks/subscriptions/{subscription_id}")
async def delete_webhook_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user)
):
    """Delete a webhook subscription"""
    
    subscription = await webhook_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Check permissions
    if not current_user.is_super_admin and subscription.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    deleted = await webhook_service.delete_subscription(subscription_id)
    if deleted:
        return {"message": "Subscription deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete subscription")


@router.get("/webhooks/subscriptions/{subscription_id}/stats")
async def get_webhook_stats(
    subscription_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get delivery statistics for a webhook"""
    
    subscription = await webhook_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Check permissions
    if not current_user.is_super_admin and subscription.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    stats = await webhook_service.get_webhook_stats(subscription_id)
    return stats


@router.get("/webhooks/deliveries/{subscription_id}")
async def get_webhook_delivery_logs(
    subscription_id: int,
    event: Optional[str] = None,
    status: Optional[str] = None,
    hours: int = Query(24, ge=1, le=720),
    current_user: User = Depends(get_current_user)
):
    """
    Get webhook delivery logs for a subscription
    
    - **subscription_id**: Webhook subscription ID
    - **event**: Filter by event type
    - **status**: Filter by delivery status
    - **hours**: Historical period
    """
    
    subscription = await webhook_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Check permissions
    if not current_user.is_super_admin and subscription.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    logs = await webhook_service.get_delivery_logs(
        subscription_id=subscription_id,
        event=event,
        status=status,
        hours=hours
    )

    return {
        "subscription_id": subscription_id,
        "delivery_logs": [
            {
                "webhook_id": log.webhook_id,
                "event": log.event,
                "status": log.status,
                "status_code": log.status_code,
                "error": log.error,
                "retry_count": log.retry_count,
                "timestamp": log.timestamp.isoformat()
            }
            for log in logs
        ]
    }


@router.get("/webhooks/test/{subscription_id}")
async def test_webhook_delivery(
    subscription_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Test webhook delivery with a sample payload
    
    - **subscription_id**: Webhook subscription ID
    """
    
    subscription = await webhook_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Check permissions
    if not current_user.is_super_admin and subscription.municipality_id != current_user.municipality_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Send test payload
    test_payload = WebhookPayload(
        event=WebhookEvent.SYSTEM_HEALTH_CHANGED,
        data={
            "test": True,
            "health_score": 95.5,
            "message": "Test webhook delivery"
        }
    )

    delivered = await webhook_service.deliver_event(test_payload)

    return {
        "subscription_id": subscription_id,
        "test_sent": True,
        "delivered_to_subscriptions": delivered,
        "timestamp": datetime.utcnow().isoformat()
    }
