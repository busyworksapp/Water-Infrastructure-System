"""Data aggregation service for time-series rollups."""
from datetime import datetime, timedelta
import logging
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.sensor import Sensor, SensorReading

logger = logging.getLogger(__name__)


class AggregationService:
    @staticmethod
    def _bucket_expression(db: Session, column, granularity: str):
        dialect = db.bind.dialect.name if db.bind else "postgresql"

        if dialect.startswith("postgres"):
            return func.date_trunc(granularity, column)
        if dialect.startswith("mysql"):
            fmt = "%Y-%m-%d %H:00:00" if granularity == "hour" else "%Y-%m-%d 00:00:00"
            return func.date_format(column, fmt)
        if dialect.startswith("sqlite"):
            fmt = "%Y-%m-%d %H:00:00" if granularity == "hour" else "%Y-%m-%d 00:00:00"
            return func.strftime(fmt, column)
        return column

    def aggregate_hourly(self, db: Session, sensor_id: str, hours: int = 24):
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        bucket = self._bucket_expression(db, SensorReading.timestamp, "hour").label("bucket")

        rows = (
            db.query(
                bucket,
                func.avg(SensorReading.value).label("avg"),
                func.min(SensorReading.value).label("min"),
                func.max(SensorReading.value).label("max"),
                func.count(SensorReading.id).label("count"),
            )
            .filter(
                SensorReading.sensor_id == sensor_id,
                SensorReading.timestamp >= cutoff,
            )
            .group_by(bucket)
            .order_by(bucket)
            .all()
        )

        return [
            {
                "timestamp": str(row.bucket),
                "avg": float(row.avg),
                "min": float(row.min),
                "max": float(row.max),
                "count": int(row.count),
            }
            for row in rows
        ]

    def aggregate_daily(self, db: Session, sensor_id: str, days: int = 30):
        cutoff = datetime.utcnow() - timedelta(days=days)
        bucket = self._bucket_expression(db, SensorReading.timestamp, "day").label("bucket")

        rows = (
            db.query(
                bucket,
                func.avg(SensorReading.value).label("avg"),
                func.min(SensorReading.value).label("min"),
                func.max(SensorReading.value).label("max"),
                func.stddev(SensorReading.value).label("stddev"),
                func.count(SensorReading.id).label("count"),
            )
            .filter(
                SensorReading.sensor_id == sensor_id,
                SensorReading.timestamp >= cutoff,
            )
            .group_by(bucket)
            .order_by(bucket)
            .all()
        )

        return [
            {
                "date": str(row.bucket),
                "avg": float(row.avg),
                "min": float(row.min),
                "max": float(row.max),
                "stddev": float(row.stddev) if row.stddev is not None else 0.0,
                "count": int(row.count),
            }
            for row in rows
        ]

    def alert_summary(self, db: Session, municipality_id: Optional[str] = None, days: int = 7):
        cutoff = datetime.utcnow() - timedelta(days=days)

        query = (
            db.query(Alert.alert_type, Alert.severity, func.count(Alert.id).label("count"))
            .filter(Alert.created_at >= cutoff)
        )
        if municipality_id:
            query = query.filter(Alert.municipality_id == municipality_id)

        rows = query.group_by(Alert.alert_type, Alert.severity).all()
        return [
            {
                "type": row.alert_type.value if hasattr(row.alert_type, "value") else str(row.alert_type),
                "severity": row.severity.value if hasattr(row.severity, "value") else str(row.severity),
                "count": int(row.count),
            }
            for row in rows
        ]

    def sensor_uptime(self, db: Session, sensor_id: str, hours: int = 24, current_user=None):
        sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
        if not sensor:
            return {"error": "Sensor not found"}
        if current_user and not current_user.is_super_admin and sensor.municipality_id != current_user.municipality_id:
            return {"error": "Access denied"}

        cutoff = datetime.utcnow() - timedelta(hours=hours)
        reading_count = (
            db.query(func.count(SensorReading.id))
            .filter(
                SensorReading.sensor_id == sensor_id,
                SensorReading.timestamp >= cutoff,
            )
            .scalar()
            or 0
        )

        expected_interval = max(float(sensor.sampling_interval_sec or 300), 1.0)
        expected_readings = int((hours * 3600) / expected_interval)
        uptime = min((reading_count / expected_readings) * 100, 100) if expected_readings > 0 else 0

        return {
            "sensor_id": sensor_id,
            "hours": hours,
            "readings": int(reading_count),
            "expected": expected_readings,
            "uptime_percent": round(uptime, 2),
        }


aggregation_service = AggregationService()
