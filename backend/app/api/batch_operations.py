"""Batch operations and cache management API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..services.batch_processor import BatchProcessor
from ..services.cache_warmer import CacheWarmer

router = APIRouter(prefix="/api/v1/batch", tags=["batch-operations"])

class ReadingBatch(BaseModel):
    sensor_id: str
    value: float
    unit: str = "bar"
    timestamp: str = None

class SensorUpdate(BaseModel):
    sensor_id: str
    name: str = None
    is_active: bool = None

@router.post("/readings")
async def bulk_insert_readings(
    readings: List[ReadingBatch],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk insert sensor readings."""
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    processor = BatchProcessor(db)
    result = processor.bulk_insert_readings([r.dict() for r in readings])
    return result

@router.post("/sensors/update")
async def bulk_update_sensors(
    updates: List[SensorUpdate],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk update sensors."""
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    processor = BatchProcessor(db)
    result = processor.bulk_update_sensors([u.dict(exclude_none=True) for u in updates])
    return result

@router.post("/alerts/resolve")
async def bulk_resolve_alerts(
    alert_ids: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk resolve alerts."""
    processor = BatchProcessor(db)
    result = processor.bulk_resolve_alerts(alert_ids, current_user.id)
    return result

@router.post("/cache/warm")
async def warm_cache(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Warm all caches."""
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    warmer = CacheWarmer(db)
    result = warmer.warm_all()
    return {"status": "completed", "results": result}
