from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

from sqlalchemy.orm import Session

from ..models.alert import Alert, AlertSeverity, AlertStatus, AlertType
from ..models.sensor import Sensor, SensorReading
from ..models.system import DynamicRule

logger = logging.getLogger(__name__)


class AlertService:
    def __init__(self):
        self.cooldown_cache: Dict[str, datetime] = {}

    def create_alert_from_reading(
        self,
        db: Session,
        sensor: Sensor,
        reading: SensorReading,
        anomaly_score: float,
    ) -> Optional[Alert]:
        alert_type = self._determine_alert_type(sensor)
        cooldown_key = self._cooldown_key(sensor, alert_type.value)
        if not self._cooldown_passed(cooldown_key, cooldown_seconds=300):
            return None

        severity = self._determine_severity(anomaly_score)
        alert = Alert(
            municipality_id=sensor.municipality_id,
            sensor_id=sensor.id,
            pipeline_id=sensor.pipeline_id,
            alert_type=alert_type,
            severity=severity,
            status=AlertStatus.OPEN,
            title=f"{alert_type.value.replace('_', ' ').title()} detected on {sensor.name}",
            description=f"Anomalous reading detected: {reading.value} {reading.unit or ''}".strip(),
            location=sensor.location,
            triggered_value={"value": reading.value, "unit": reading.unit},
            metadata_json={
                "anomaly_score": anomaly_score,
                "reading_id": reading.id,
                "timestamp": reading.timestamp.isoformat(),
            },
        )
        db.add(alert)
        db.flush()
        self._set_cooldown(cooldown_key, seconds=300)
        self._broadcast_alert(sensor, alert)
        return alert

    def create_alert_from_rule(
        self,
        db: Session,
        sensor: Sensor,
        reading: SensorReading,
        rule: DynamicRule,
    ) -> Optional[Alert]:
        cooldown_key = self._cooldown_key(sensor, f"rule:{rule.id}")
        cooldown_seconds = int(rule.cooldown_seconds or 300)
        if not self._cooldown_passed(cooldown_key, cooldown_seconds=cooldown_seconds):
            return None

        try:
            alert_type = AlertType(rule.alert_type.lower())
        except Exception:
            alert_type = AlertType.CUSTOM

        try:
            severity = AlertSeverity(rule.alert_severity.lower())
        except Exception:
            severity = AlertSeverity.MEDIUM

        template = rule.alert_template or {}
        alert = Alert(
            municipality_id=sensor.municipality_id,
            sensor_id=sensor.id,
            pipeline_id=sensor.pipeline_id,
            alert_type=alert_type,
            severity=severity,
            status=AlertStatus.OPEN,
            title=template.get("title") or f"Rule triggered: {rule.name}",
            description=template.get("description") or rule.description,
            location=sensor.location,
            rule_id=rule.id,
            triggered_value={"value": reading.value, "unit": reading.unit},
            threshold_value=rule.conditions,
            metadata_json={
                "rule_name": rule.name,
                "reading_id": reading.id,
                "timestamp": reading.timestamp.isoformat(),
            },
        )
        db.add(alert)
        db.flush()
        self._set_cooldown(cooldown_key, seconds=cooldown_seconds)
        self._broadcast_alert(sensor, alert)
        return alert

    @staticmethod
    def _determine_alert_type(sensor: Sensor) -> AlertType:
        sensor_type_code = (sensor.sensor_type.code or "").lower()
        if "pressure" in sensor_type_code:
            return AlertType.PRESSURE_ANOMALY
        if "flow" in sensor_type_code:
            return AlertType.FLOW_IRREGULARITY
        if "leak" in sensor_type_code:
            return AlertType.LEAK
        if "burst" in sensor_type_code:
            return AlertType.BURST
        return AlertType.CUSTOM

    @staticmethod
    def _determine_severity(anomaly_score: float) -> AlertSeverity:
        if anomaly_score >= 0.9:
            return AlertSeverity.CRITICAL
        if anomaly_score >= 0.7:
            return AlertSeverity.HIGH
        if anomaly_score >= 0.5:
            return AlertSeverity.MEDIUM
        if anomaly_score >= 0.3:
            return AlertSeverity.LOW
        return AlertSeverity.INFO

    @staticmethod
    def _cooldown_key(sensor: Sensor, alert_key: str) -> str:
        return f"{sensor.municipality_id}:{sensor.id}:{alert_key}"

    def _cooldown_passed(self, cache_key: str, cooldown_seconds: int) -> bool:
        expiration = self.cooldown_cache.get(cache_key)
        if not expiration:
            return True
        return datetime.utcnow() >= expiration

    def _set_cooldown(self, cache_key: str, seconds: int):
        self.cooldown_cache[cache_key] = datetime.utcnow() + timedelta(seconds=seconds)

    @staticmethod
    def _broadcast_alert(sensor: Sensor, alert: Alert):
        try:
            from ..websocket.manager import ws_manager

            ws_manager.broadcast_alert(
                sensor.municipality_id,
                {
                    "id": alert.id,
                    "type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "sensor_id": sensor.id,
                    "timestamp": alert.created_at.isoformat() if alert.created_at else datetime.utcnow().isoformat(),
                },
            )
        except Exception as exc:
            logger.warning("Failed to broadcast alert %s: %s", alert.id, exc)
