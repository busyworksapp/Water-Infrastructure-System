"""LoRaWAN gateway integration."""
from __future__ import annotations

import logging
from typing import Dict

from app.core.database import SessionLocal
from app.services.ingestion_service import ingestion_service

logger = logging.getLogger(__name__)


class LoRaWANGateway:
    def decode_payload(self, payload: bytes, codec: str = "cayenne") -> Dict:
        if codec == "cayenne":
            return self._decode_cayenne_lpp(payload)
        if codec == "raw":
            return self._decode_raw(payload)
        raise ValueError(f"Unsupported codec: {codec}")

    def _decode_cayenne_lpp(self, payload: bytes) -> Dict:
        data: Dict[str, float] = {}
        idx = 0
        while idx < len(payload) - 1:
            channel = payload[idx]
            data_type = payload[idx + 1]
            if data_type == 0x02 and idx + 3 < len(payload):
                value = int.from_bytes(payload[idx + 2 : idx + 4], "big", signed=True) / 100
                data[f"channel_{channel}"] = value
                idx += 4
            elif data_type == 0x67 and idx + 3 < len(payload):
                value = int.from_bytes(payload[idx + 2 : idx + 4], "big", signed=True) / 10
                data[f"temperature_{channel}"] = value
                idx += 4
            else:
                idx += 1
        return data

    @staticmethod
    def _decode_raw(payload: bytes) -> Dict:
        if len(payload) >= 4:
            return {"value": int.from_bytes(payload[:4], "big", signed=True) / 100}
        return {}

    async def process_uplink(self, device_eui: str, payload: bytes, metadata: Dict):
        db = SessionLocal()
        try:
            decoded = self.decode_payload(payload, codec="cayenne")
            value = decoded.get("value")
            if value is None and decoded:
                value = next(iter(decoded.values()))
            if value is None:
                raise ValueError("Decoded payload contained no numeric reading")

            reading_payload = {
                "value": value,
                "timestamp": metadata.get("timestamp"),
                "quality_score": self._calculate_quality(metadata),
                "decoded_payload": decoded,
                "rssi": metadata.get("rssi"),
                "snr": metadata.get("snr"),
                "frequency": metadata.get("frequency"),
            }

            result = ingestion_service.process_reading(
                db,
                device_id=device_eui,
                protocol="lorawan",
                payload=reading_payload,
                certificate_fingerprint=metadata.get("certificate_fingerprint"),
                enforce_api_key=False,
            )
            logger.info("LoRaWAN uplink processed for %s", device_eui)
            return result
        except Exception as exc:
            db.rollback()
            logger.error("LoRaWAN uplink processing failed for %s: %s", device_eui, exc)
            raise
        finally:
            db.close()

    @staticmethod
    def _calculate_quality(metadata: Dict) -> float:
        rssi = float(metadata.get("rssi", -120))
        snr = float(metadata.get("snr", -20))
        rssi_score = max(0.0, min(1.0, (rssi + 120) / 60))
        snr_score = max(0.0, min(1.0, (snr + 20) / 30))
        return round((rssi_score + snr_score) / 2, 4)


lorawan_gateway = LoRaWANGateway()
