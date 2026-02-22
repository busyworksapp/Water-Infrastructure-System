from __future__ import annotations

from datetime import datetime
import hashlib
import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from ..models.device_auth import DeviceAuthentication
from ..models.sensor import Sensor, SensorReading
from .alert_service import AlertService
from .anomaly_detector import anomaly_detector
from .audit_service import audit_service
from .protocol_service import protocol_service

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self):
        self.alert_service = AlertService()

    def process_reading(
        self,
        db: Session,
        *,
        device_id: str,
        protocol: str,
        payload: Dict[str, Any],
        api_key: Optional[str] = None,
        mqtt_password: Optional[str] = None,
        certificate_fingerprint: Optional[str] = None,
        enforce_api_key: bool = False,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        sensor = db.query(Sensor).filter(Sensor.device_id == device_id).first()
        if not sensor:
            raise ValueError(f"Sensor not found for device {device_id}")

        if not protocol_service.is_protocol_enabled(db, protocol, sensor.municipality_id):
            raise PermissionError(f"Protocol '{protocol}' is disabled")

        device_auth = self._validate_device(
            db,
            sensor=sensor,
            api_key=api_key,
            mqtt_password=mqtt_password,
            certificate_fingerprint=certificate_fingerprint,
            enforce_api_key=enforce_api_key,
        )

        reading = SensorReading(
            sensor_id=sensor.id,
            timestamp=self._parse_timestamp(payload.get("timestamp")),
            value=float(payload["value"]),
            unit=str(payload.get("unit") or (sensor.sensor_type.unit if sensor.sensor_type else "")),
            quality_score=float(payload.get("quality_score", payload.get("quality", 1.0))),
            raw_data=payload,
        )

        db.add(reading)
        db.flush()

        sensor.last_reading_at = reading.timestamp
        if payload.get("battery_level") is not None:
            sensor.battery_level = float(payload["battery_level"])
        if payload.get("signal_strength") is not None:
            sensor.signal_strength = float(payload["signal_strength"])

        is_anomaly, anomaly_score = anomaly_detector.detect(sensor, reading, db)
        reading.is_anomaly = is_anomaly

        alerts = []
        if is_anomaly:
            alert = self.alert_service.create_alert_from_reading(db, sensor, reading, anomaly_score)
            if alert:
                alerts.append(alert)

        dynamic_rules = anomaly_detector.check_dynamic_rules(db, sensor, reading)
        for rule in dynamic_rules:
            alert = self.alert_service.create_alert_from_rule(db, sensor, reading, rule)
            if alert:
                alerts.append(alert)

        if device_auth:
            device_auth.last_authenticated = datetime.utcnow()

        audit_service.log(
            db,
            action="sensor.reading_ingested",
            resource_type="sensor_reading",
            resource_id=reading.id,
            description=f"{protocol.upper()} reading ingested from {device_id}",
            municipality_id=sensor.municipality_id,
            ip_address=source_ip,
            user_agent=user_agent,
            changes={"value": reading.value, "is_anomaly": reading.is_anomaly},
            metadata={"protocol": protocol, "alert_count": len(alerts)},
        )

        db.commit()

        self._broadcast(sensor, reading, alerts)

        return {
            "status": "success",
            "reading_id": reading.id,
            "sensor_id": sensor.id,
            "is_anomaly": is_anomaly,
            "anomaly_score": anomaly_score,
            "triggered_alert_ids": [alert.id for alert in alerts],
        }

    @staticmethod
    def _validate_device(
        db: Session,
        *,
        sensor: Sensor,
        api_key: Optional[str],
        mqtt_password: Optional[str],
        certificate_fingerprint: Optional[str],
        enforce_api_key: bool,
    ) -> Optional[DeviceAuthentication]:
        auth = db.query(DeviceAuthentication).filter(
            DeviceAuthentication.device_id == sensor.device_id,
            DeviceAuthentication.sensor_id == sensor.id,
            DeviceAuthentication.is_active.is_(True),
        ).first()

        if not auth:
            raise PermissionError("Device authentication record not found or inactive")

        if auth.expires_at and auth.expires_at <= datetime.utcnow():
            raise PermissionError("Device credentials expired")

        if enforce_api_key and not api_key:
            raise PermissionError("API key is required")

        if api_key and auth.api_key and auth.api_key != api_key:
            raise PermissionError("Invalid API key")

        if mqtt_password and auth.mqtt_password_hash:
            supplied_hash = hashlib.sha256(mqtt_password.encode()).hexdigest()
            if supplied_hash != auth.mqtt_password_hash:
                raise PermissionError("Invalid MQTT password")

        if certificate_fingerprint and auth.certificate_fingerprint:
            if certificate_fingerprint != auth.certificate_fingerprint:
                raise PermissionError("Invalid certificate fingerprint")

        return auth

    @staticmethod
    def _parse_timestamp(timestamp_value: Any) -> datetime:
        if not timestamp_value:
            return datetime.utcnow()
        if isinstance(timestamp_value, datetime):
            return timestamp_value
        if isinstance(timestamp_value, str):
            return datetime.fromisoformat(timestamp_value.replace("Z", "+00:00"))
        raise ValueError("Unsupported timestamp type")

    @staticmethod
    def _broadcast(sensor: Sensor, reading: SensorReading, alerts):
        from ..websocket.manager import ws_manager

        ws_manager.broadcast_sensor_reading(
            sensor.municipality_id,
            {
                "sensor_id": sensor.id,
                "device_id": sensor.device_id,
                "value": reading.value,
                "unit": reading.unit,
                "timestamp": reading.timestamp.isoformat(),
                "is_anomaly": reading.is_anomaly,
                "quality_score": reading.quality_score,
            },
        )
        ws_manager.add_event(
            sensor.municipality_id,
            {
                "event_type": "sensor_reading",
                "sensor_id": sensor.id,
                "reading_id": reading.id,
                "timestamp": reading.timestamp.isoformat(),
                "value": reading.value,
                "is_anomaly": reading.is_anomaly,
                "alerts": [alert.id for alert in alerts],
            },
        )


ingestion_service = IngestionService()
