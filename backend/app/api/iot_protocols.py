"""IoT protocols API endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, get_current_super_admin
from app.iot.lorawan import lorawan_gateway
from app.iot.nbiot import nbiot_gateway
from app.models.system import ProtocolConfiguration, ProtocolType
from app.models.user import User

router = APIRouter(prefix="/api/v1/iot", tags=["iot-protocols"])


class LoRaWANUplink(BaseModel):
    device_eui: str
    payload: str = Field(description="Hex-encoded payload")
    rssi: Optional[int] = -120
    snr: Optional[float] = -20
    frequency: Optional[float] = None
    timestamp: Optional[str] = None
    certificate_fingerprint: Optional[str] = None


class NBIoTMessage(BaseModel):
    imei: str
    value: float
    signal_strength: Optional[int] = 0
    battery_level: Optional[int] = 100
    timestamp: Optional[str] = None
    api_key: Optional[str] = None


class UpdateProtocolConfigRequest(BaseModel):
    municipality_id: Optional[str] = None
    is_enabled: bool
    settings: dict = Field(default_factory=dict)


@router.post("/lorawan/uplink")
async def lorawan_uplink(uplink: LoRaWANUplink):
    try:
        payload_bytes = bytes.fromhex(uplink.payload)
        metadata = {
            "rssi": uplink.rssi,
            "snr": uplink.snr,
            "frequency": uplink.frequency,
            "timestamp": uplink.timestamp,
            "certificate_fingerprint": uplink.certificate_fingerprint,
        }
        result = await lorawan_gateway.process_uplink(uplink.device_eui, payload_bytes, metadata)
        return {"status": "success", **result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"LoRaWAN processing failed: {exc}")


@router.post("/nbiot/message")
async def nbiot_message(message: NBIoTMessage):
    try:
        return await nbiot_gateway.process_message(message.imei, message.dict())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"NB-IoT processing failed: {exc}")


@router.get("/protocols")
def list_protocols(
    municipality_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_super_admin:
        municipality_id = current_user.municipality_id

    configured = {
        (cfg.protocol.value, cfg.municipality_id): cfg
        for cfg in db.query(ProtocolConfiguration).all()
    }

    result = []
    for protocol in ProtocolType:
        scoped = configured.get((protocol.value, municipality_id))
        global_cfg = configured.get((protocol.value, None))
        active_cfg = scoped or global_cfg
        result.append(
            {
                "protocol": protocol.value,
                "municipality_id": municipality_id,
                "is_enabled": bool(active_cfg.is_enabled) if active_cfg else True,
                "settings": active_cfg.settings if active_cfg else {},
                "scope": "municipality" if scoped else "global",
            }
        )
    return {"protocols": result}


@router.put("/protocols/{protocol}")
def update_protocol(
    protocol: ProtocolType,
    request: UpdateProtocolConfigRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    config = (
        db.query(ProtocolConfiguration)
        .filter(
            ProtocolConfiguration.protocol == protocol,
            ProtocolConfiguration.municipality_id == request.municipality_id,
        )
        .first()
    )
    if not config:
        config = ProtocolConfiguration(
            protocol=protocol,
            municipality_id=request.municipality_id,
            is_enabled=request.is_enabled,
            settings=request.settings,
        )
        db.add(config)
    else:
        config.is_enabled = request.is_enabled
        config.settings = request.settings or {}

    db.commit()
    db.refresh(config)
    return {
        "id": config.id,
        "protocol": config.protocol.value,
        "municipality_id": config.municipality_id,
        "is_enabled": config.is_enabled,
        "settings": config.settings,
    }
