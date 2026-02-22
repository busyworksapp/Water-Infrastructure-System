from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.models.sensor import Sensor, SensorReading, SensorStatus
from app.models.alert import Alert, AlertStatus, AlertSeverity
from app.models.municipality import Municipality
from app.services.cache_service import cache_service
import logging

logger = logging.getLogger(__name__)

class DashboardService:

    def get_system_overview(self, db: Session):
        cache_key = "dashboard:system_overview"
        cached = cache_service.get(cache_key)
        if cached:
            return cached

        total_sensors = db.query(func.count(Sensor.id)).scalar() or 0
        active_sensors = db.query(func.count(Sensor.id)).filter(
            Sensor.status == SensorStatus.ACTIVE
        ).scalar() or 0
        total_municipalities = db.query(func.count(Municipality.id)).scalar() or 0

        cutoff = datetime.utcnow() - timedelta(hours=24)
        active_alerts = db.query(func.count(Alert.id)).filter(
            Alert.created_at >= cutoff,
            Alert.status.notin_([AlertStatus.RESOLVED, AlertStatus.CLOSED])
        ).scalar() or 0

        critical_alerts = db.query(func.count(Alert.id)).filter(
            Alert.created_at >= cutoff,
            Alert.severity == AlertSeverity.CRITICAL,
            Alert.status.notin_([AlertStatus.RESOLVED, AlertStatus.CLOSED])
        ).scalar() or 0

        data = {
            "total_sensors": total_sensors,
            "active_sensors": active_sensors,
            "inactive_sensors": total_sensors - active_sensors,
            "total_municipalities": total_municipalities,
            "active_alerts": active_alerts,
            "critical_alerts": critical_alerts,
            "system_health": self._calculate_system_health(active_sensors, total_sensors, critical_alerts)
        }

        cache_service.set(cache_key, data, ttl=60)
        return data

    def get_municipality_dashboard(self, db: Session, municipality_id: str):
        cache_key = f"dashboard:municipality:{municipality_id}"
        cached = cache_service.get(cache_key)
        if cached:
            return cached

        sensors = db.query(Sensor).filter(Sensor.municipality_id == municipality_id).all()
        sensor_ids = [s.id for s in sensors]

        cutoff = datetime.utcnow() - timedelta(hours=24)

        recent_readings = 0
        if sensor_ids:
            recent_readings = db.query(func.count(SensorReading.id)).filter(
                SensorReading.sensor_id.in_(sensor_ids),
                SensorReading.timestamp >= cutoff
            ).scalar() or 0

        alerts = db.query(Alert).filter(
            Alert.municipality_id == municipality_id,
            Alert.created_at >= cutoff
        ).all()

        data = {
            "municipality_id": municipality_id,
            "total_sensors": len(sensors),
            "active_sensors": sum(1 for s in sensors if s.status == SensorStatus.ACTIVE),
            "recent_readings": recent_readings,
            "total_alerts": len(alerts),
            "unresolved_alerts": sum(
                1 for a in alerts
                if a.status not in (AlertStatus.RESOLVED, AlertStatus.CLOSED)
            ),
            "alert_breakdown": self._alert_breakdown(alerts)
        }

        cache_service.set(cache_key, data, ttl=120)
        return data

    def get_sensor_health_summary(self, db: Session, municipality_id: str = None):
        query = db.query(Sensor)
        if municipality_id:
            query = query.filter(Sensor.municipality_id == municipality_id)

        sensors = query.all()
        cutoff = datetime.utcnow() - timedelta(hours=1)

        health_summary = {"healthy": 0, "warning": 0, "critical": 0, "offline": 0}

        for sensor in sensors:
            last_reading = db.query(SensorReading).filter(
                SensorReading.sensor_id == sensor.id
            ).order_by(SensorReading.timestamp.desc()).first()

            if not last_reading or last_reading.timestamp < cutoff:
                health_summary["offline"] += 1
            elif last_reading.quality_score and last_reading.quality_score < 0.7:
                health_summary["critical"] += 1
            elif last_reading.quality_score and last_reading.quality_score < 0.9:
                health_summary["warning"] += 1
            else:
                health_summary["healthy"] += 1

        return health_summary

    def get_recent_activity(self, db: Session, municipality_id: str = None, limit: int = 10):
        query = db.query(Alert).order_by(Alert.created_at.desc())

        if municipality_id:
            query = query.filter(Alert.municipality_id == municipality_id)

        alerts = query.limit(limit).all()

        return [{
            "id": a.id,
            "type": a.alert_type.value,
            "severity": a.severity.value,
            "title": a.title,
            "description": a.description,
            "sensor_id": a.sensor_id,
            "created_at": a.created_at.isoformat(),
            "status": a.status.value
        } for a in alerts]

    def _calculate_system_health(self, active: int, total: int, critical: int):
        if total == 0:
            return 100
        uptime_score = (active / total) * 100
        alert_penalty = min(critical * 5, 30)
        return max(0, min(100, uptime_score - alert_penalty))

    def _alert_breakdown(self, alerts):
        breakdown = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for alert in alerts:
            key = alert.severity.value if hasattr(alert.severity, 'value') else str(alert.severity)
            if key in breakdown:
                breakdown[key] += 1
        return breakdown

dashboard_service = DashboardService()
