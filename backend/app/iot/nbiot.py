"""NB-IoT integration for cellular sensors."""
from __future__ import annotations

import logging
from typing import Dict

from app.core.database import SessionLocal
from app.services.ingestion_service import ingestion_service

logger = logging.getLogger(__name__)


class NBIoTGateway:
    async def process_message(self, imei: str, data: Dict):
        db = SessionLocal()
        try:
            if data.get("value") is None:
                raise ValueError("Missing value in NB-IoT payload")

            payload = {
                "value": data.get("value"),
                "timestamp": data.get("timestamp"),
                "quality_score": self._calculate_quality(data),
                "signal_strength": data.get("signal_strength"),
                "battery_level": data.get("battery_level"),
                "raw_message": data,
            }

            result = ingestion_service.process_reading(
                db,
                device_id=imei,
                protocol="nbiot",
                payload=payload,
                api_key=data.get("api_key"),
                enforce_api_key=False,
            )
            return {"status": "success", **result}
        except Exception as exc:
            db.rollback()
            logger.error("NB-IoT message processing failed for %s: %s", imei, exc)
            return {"status": "error", "message": str(exc)}
        finally:
            db.close()

    @staticmethod
    def _calculate_quality(data: Dict) -> float:
        signal = float(data.get("signal_strength", 0))
        battery = float(data.get("battery_level", 100))
        signal_score = max(0.0, min(1.0, signal / 100))
        battery_score = max(0.0, min(1.0, battery / 100))
        return round((signal_score * 0.6) + (battery_score * 0.4), 4)


nbiot_gateway = NBIoTGateway()
