from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
import logging
import math

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..models.sensor import Sensor, SensorReading
from ..models.system import DynamicRule

logger = logging.getLogger(__name__)


class AnomalyDetector:
    def __init__(self):
        self.lookback_hours = 24
        self.std_threshold = 3.0
        self.min_samples = 10

    def detect(self, sensor: Sensor, reading: SensorReading, db: Session | None = None) -> Tuple[bool, float]:
        """
        Detect anomalies using a layered strategy:
        1) Z-score outlier detection over lookback window
        2) Rate-of-change anomaly detection
        3) Domain-specific pressure/flow checks
        """
        managed_session = False
        session = db
        if session is None:
            session = SessionLocal()
            managed_session = True

        try:
            anomaly_score = 0.0
            is_anomaly = False

            checks = [
                self._statistical_detection(session, sensor, reading),
                self._rate_of_change_detection(session, sensor, reading),
                self._pressure_drop_detection(session, sensor, reading),
                self._flow_irregularity_detection(session, sensor, reading),
            ]
            for detected, score in checks:
                if detected:
                    is_anomaly = True
                    anomaly_score = max(anomaly_score, score)

            return is_anomaly, round(float(anomaly_score), 4)
        except Exception as exc:
            logger.error("Anomaly detection failed for sensor %s: %s", sensor.id, exc)
            return False, 0.0
        finally:
            if managed_session:
                session.close()

    def _statistical_detection(
        self, db: Session, sensor: Sensor, reading: SensorReading
    ) -> Tuple[bool, float]:
        cutoff_time = reading.timestamp - timedelta(hours=self.lookback_hours)
        historical = (
            db.query(SensorReading.value)
            .filter(
                SensorReading.sensor_id == sensor.id,
                SensorReading.timestamp >= cutoff_time,
                SensorReading.timestamp < reading.timestamp,
                SensorReading.is_anomaly.is_(False),
            )
            .all()
        )
        if len(historical) < self.min_samples:
            return False, 0.0

        values = [float(row[0]) for row in historical]
        if HAS_NUMPY:
            mean = np.mean(values)
            std = np.std(values)
        else:
            mean = sum(values) / len(values)
            std = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5
        if std <= 1e-9:
            return False, 0.0

        z_score = abs((reading.value - mean) / std)
        if z_score <= self.std_threshold:
            return False, 0.0

        return True, min(z_score / 8.0, 1.0)

    def _rate_of_change_detection(
        self, db: Session, sensor: Sensor, reading: SensorReading
    ) -> Tuple[bool, float]:
        previous = (
            db.query(SensorReading)
            .filter(
                SensorReading.sensor_id == sensor.id,
                SensorReading.timestamp < reading.timestamp,
            )
            .order_by(SensorReading.timestamp.desc())
            .first()
        )
        if not previous:
            return False, 0.0

        elapsed_seconds = max((reading.timestamp - previous.timestamp).total_seconds(), 1.0)
        value_delta = abs(reading.value - previous.value)
        rate_per_sec = value_delta / elapsed_seconds

        threshold_config = sensor.sensor_type.threshold_config or {}
        max_rate = float(threshold_config.get("max_rate_of_change", math.inf))
        if math.isinf(max_rate) or max_rate <= 0:
            return False, 0.0

        if rate_per_sec <= max_rate:
            return False, 0.0

        return True, min(rate_per_sec / max_rate, 1.0)

    def _pressure_drop_detection(
        self, db: Session, sensor: Sensor, reading: SensorReading
    ) -> Tuple[bool, float]:
        sensor_code = (sensor.sensor_type.code or "").lower()
        if "pressure" not in sensor_code:
            return False, 0.0

        window_start = reading.timestamp - timedelta(minutes=15)
        history = (
            db.query(SensorReading.value)
            .filter(
                SensorReading.sensor_id == sensor.id,
                SensorReading.timestamp >= window_start,
                SensorReading.timestamp < reading.timestamp,
            )
            .order_by(SensorReading.timestamp.asc())
            .all()
        )
        if len(history) < 3:
            return False, 0.0

        if HAS_NUMPY:
            baseline = float(np.mean([float(row[0]) for row in history]))
        else:
            vals = [float(row[0]) for row in history]
            baseline = sum(vals) / len(vals)
        if baseline <= 0:
            return False, 0.0

        drop_ratio = (baseline - reading.value) / baseline
        if drop_ratio < 0.25:
            return False, 0.0

        return True, min(drop_ratio, 1.0)

    def _flow_irregularity_detection(
        self, db: Session, sensor: Sensor, reading: SensorReading
    ) -> Tuple[bool, float]:
        sensor_code = (sensor.sensor_type.code or "").lower()
        if "flow" not in sensor_code:
            return False, 0.0

        window_start = reading.timestamp - timedelta(hours=2)
        history = (
            db.query(SensorReading.value)
            .filter(
                SensorReading.sensor_id == sensor.id,
                SensorReading.timestamp >= window_start,
                SensorReading.timestamp < reading.timestamp,
            )
            .all()
        )
        if len(history) < 6:
            return False, 0.0

        values = [float(row[0]) for row in history]
        if HAS_NUMPY:
            mean = float(np.mean(values))
            std = float(np.std(values))
        else:
            mean = sum(values) / len(values)
            std = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5
        if std <= 1e-9:
            return False, 0.0

        score = abs((reading.value - mean) / std)
        if score < 2.5:
            return False, 0.0

        return True, min(score / 8.0, 1.0)

    def check_dynamic_rules(self, db: Session, sensor: Sensor, reading: SensorReading) -> List[DynamicRule]:
        triggered_rules: List[DynamicRule] = []

        rules = (
            db.query(DynamicRule)
            .filter(
                DynamicRule.is_active.is_(True),
                (DynamicRule.sensor_type_id.is_(None) | (DynamicRule.sensor_type_id == sensor.sensor_type_id)),
                (
                    DynamicRule.municipality_id.is_(None)
                    | (DynamicRule.municipality_id == sensor.municipality_id)
                ),
            )
            .order_by(DynamicRule.priority.asc())
            .all()
        )

        for rule in rules:
            try:
                if self._evaluate_rule(rule, reading):
                    triggered_rules.append(rule)
            except Exception as exc:
                logger.error("Failed evaluating rule %s: %s", rule.id, exc)

        return triggered_rules

    def _evaluate_rule(self, rule: DynamicRule, reading: SensorReading) -> bool:
        conditions = rule.conditions or []
        if isinstance(conditions, dict):
            conditions = [conditions]
        if not isinstance(conditions, list) or not conditions:
            return False

        evaluations = [self._evaluate_condition(condition, reading) for condition in conditions]
        logic = (rule.condition_logic or "AND").upper()
        return all(evaluations) if logic != "OR" else any(evaluations)

    def _evaluate_condition(self, condition: Dict[str, Any], reading: SensorReading) -> bool:
        operator = str(condition.get("operator", "")).lower()
        field = condition.get("field", "value")
        threshold = condition.get("threshold")
        min_val = condition.get("min")
        max_val = condition.get("max")

        value = self._extract_value(field, reading)

        if operator == "gt":
            return value > float(threshold)
        if operator == "lt":
            return value < float(threshold)
        if operator == "gte":
            return value >= float(threshold)
        if operator == "lte":
            return value <= float(threshold)
        if operator == "eq":
            return value == float(threshold)
        if operator == "neq":
            return value != float(threshold)
        if operator == "between":
            return float(min_val) <= value <= float(max_val)
        if operator == "change_rate":
            rate = float(reading.raw_data.get("change_rate", 0.0)) if reading.raw_data else 0.0
            return rate > float(threshold)
        if operator == "delta":
            delta = float(reading.raw_data.get("delta", 0.0)) if reading.raw_data else 0.0
            return abs(delta) > float(threshold)
        return False

    @staticmethod
    def _extract_value(field: str, reading: SensorReading) -> float:
        if field == "value":
            return float(reading.value)
        if reading.raw_data and field in reading.raw_data:
            return float(reading.raw_data[field])
        return float(reading.value)


anomaly_detector = AnomalyDetector()
