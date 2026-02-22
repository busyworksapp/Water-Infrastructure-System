from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..services.ingestion_service import ingestion_service

router = APIRouter(prefix="/ingest", tags=["Data Ingestion"])


class SensorDataPayload(BaseModel):
    timestamp: Optional[datetime] = None
    value: float
    unit: Optional[str] = None
    quality: float = Field(default=1.0, ge=0, le=1)
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None
    raw_data: dict = Field(default_factory=dict)


@router.post("/sensors/{device_id}/data")
async def ingest_sensor_data(
    device_id: str,
    payload: SensorDataPayload,
    request: Request,
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    api_key = None
    if authorization:
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authorization must use Bearer token")
        api_key = authorization.replace("Bearer ", "", 1).strip()

    merged_payload = {
        "timestamp": payload.timestamp.isoformat() if payload.timestamp else datetime.utcnow().isoformat(),
        "value": payload.value,
        "unit": payload.unit,
        "quality_score": payload.quality,
        "battery_level": payload.battery_level,
        "signal_strength": payload.signal_strength,
        **(payload.raw_data or {}),
    }

    try:
        result = ingestion_service.process_reading(
            db,
            device_id=device_id,
            protocol="http",
            payload=merged_payload,
            api_key=api_key,
            enforce_api_key=True,
            source_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return result
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}")

