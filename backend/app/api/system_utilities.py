"""System utilities API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import io

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.webhook import Webhook
from ..services.performance_monitor import performance_monitor
from ..services.data_export_service import DataExportService
from ..services.webhook_manager import WebhookManager
from ..services.system_health_monitor import get_system_health_monitor

router = APIRouter(prefix="/api/v1/system", tags=["system-utilities"])


# Performance Monitoring Endpoints
@router.get("/performance/endpoints")
async def get_endpoint_performance(
    endpoint: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get performance statistics for API endpoints."""
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if endpoint:
        return performance_monitor.get_endpoint_stats(endpoint)
    else:
        return {"message": "Specify endpoint parameter"}


@router.get("/performance/slow-endpoints")
async def get_slow_endpoints(
    threshold_ms: float = Query(1000, ge=100, le=10000),
    current_user: User = Depends(get_current_user)
):
    """Get list of slow endpoints."""
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    slow = performance_monitor.get_slow_endpoints(threshold_ms)
    return {"threshold_ms": threshold_ms, "slow_endpoints": slow, "total": len(slow)}


# Health Monitoring Endpoints
@router.get("/health/comprehensive")
async def get_comprehensive_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive system health report."""
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    monitor = get_system_health_monitor(db)
    return monitor.get_comprehensive_health()


# Data Export Endpoints
@router.get("/export/sensor-readings/{sensor_id}")
async def export_sensor_readings(
    sensor_id: str,
    start_date: datetime,
    end_date: datetime,
    format: str = Query("csv", regex="^(csv|json)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export sensor readings for date range."""
    from ..models.sensor import Sensor
    
    sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    if not current_user.is_super_admin and current_user.municipality_id != sensor.municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    export_service = DataExportService(db)
    data = export_service.export_sensor_readings(sensor_id, start_date, end_date, format)
    
    media_type = "text/csv" if format == "csv" else "application/json"
    filename = f"sensor_{sensor_id}_{start_date.date()}_{end_date.date()}.{format}"
    
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/alerts")
async def export_alerts(
    municipality_id: str,
    start_date: datetime,
    end_date: datetime,
    format: str = Query("csv", regex="^(csv|json)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export alerts for municipality."""
    if not current_user.is_super_admin and current_user.municipality_id != municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    export_service = DataExportService(db)
    data = export_service.export_alerts(municipality_id, start_date, end_date, format)
    
    media_type = "text/csv" if format == "csv" else "application/json"
    filename = f"alerts_{municipality_id}_{start_date.date()}_{end_date.date()}.{format}"
    
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/maintenance-logs")
async def export_maintenance_logs(
    municipality_id: str,
    start_date: datetime,
    end_date: datetime,
    format: str = Query("csv", regex="^(csv|json)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export maintenance logs."""
    if not current_user.is_super_admin and current_user.municipality_id != municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    export_service = DataExportService(db)
    data = export_service.export_maintenance_logs(municipality_id, start_date, end_date, format)
    
    media_type = "text/csv" if format == "csv" else "application/json"
    filename = f"maintenance_{municipality_id}_{start_date.date()}_{end_date.date()}.{format}"
    
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/compliance-report")
async def export_compliance_report(
    municipality_id: str,
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020, le=2100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate monthly compliance report."""
    if not current_user.is_super_admin and current_user.municipality_id != municipality_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    export_service = DataExportService(db)
    data = export_service.export_compliance_report(municipality_id, month, year)
    
    filename = f"compliance_{municipality_id}_{year}_{month:02d}.json"
    
    return Response(
        content=data,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# Webhook Management Endpoints
@router.post("/webhooks")
async def create_webhook(
    name: str,
    url: str,
    events: list,
    secret: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new webhook subscription."""
    webhook = Webhook(
        municipality_id=current_user.municipality_id,
        name=name,
        url=url,
        secret=secret,
        events=events
    )
    db.add(webhook)
    db.commit()
    db.refresh(webhook)
    
    return {"id": webhook.id, "name": webhook.name, "status": "created"}


@router.get("/webhooks")
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all webhooks for municipality."""
    webhooks = db.query(Webhook).filter(
        Webhook.municipality_id == current_user.municipality_id
    ).all()
    
    return {"webhooks": [
        {
            "id": w.id,
            "name": w.name,
            "url": w.url,
            "events": w.events,
            "is_active": w.is_active,
            "created_at": w.created_at
        } for w in webhooks
    ]}


@router.get("/webhooks/{webhook_id}/stats")
async def get_webhook_stats(
    webhook_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get webhook delivery statistics."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    if webhook.municipality_id != current_user.municipality_id and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    manager = WebhookManager(db)
    return manager.get_webhook_stats(webhook_id)


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete webhook subscription."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    if webhook.municipality_id != current_user.municipality_id and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(webhook)
    db.commit()
    
    return {"status": "deleted", "webhook_id": webhook_id}
