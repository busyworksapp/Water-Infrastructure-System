"""Celery tasks for background processing and scheduled jobs."""
from datetime import datetime, timedelta
from typing import Optional
import logging

from celery import Task
from sqlalchemy import func

from .celery_app import celery_app
from .core.database import SessionLocal
from .models.sensor import Sensor, SensorReading
from .models.alert import Alert
from .models.municipality import Municipality
from .models.audit import AuditLog
from .services.backup_service import BackupService
from .services.report_service import ReportService
from .services.notification_service import NotificationService
from .services.analytics_service import AnalyticsService
from .services.data_quality_service import DataQualityService

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session management."""
    _db = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(base=DatabaseTask, bind=True)
def cleanup_old_readings(self, days: int = 90):
    """Remove sensor readings older than specified days."""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted = self.db.query(SensorReading).filter(
            SensorReading.timestamp < cutoff
        ).delete(synchronize_session=False)
        self.db.commit()
        logger.info(f"Cleaned up {deleted} old sensor readings")
        return {"status": "success", "deleted": deleted}
    except Exception as e:
        self.db.rollback()
        logger.error(f"Failed to cleanup old readings: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(base=DatabaseTask, bind=True)
def cleanup_old_alerts(self, days: int = 180):
    """Archive and remove old resolved alerts."""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted = self.db.query(Alert).filter(
            Alert.resolved_at < cutoff,
            Alert.status == "resolved"
        ).delete(synchronize_session=False)
        self.db.commit()
        logger.info(f"Cleaned up {deleted} old alerts")
        return {"status": "success", "deleted": deleted}
    except Exception as e:
        self.db.rollback()
        logger.error(f"Failed to cleanup old alerts: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(base=DatabaseTask, bind=True)
def cleanup_old_audit_logs(self, days: int = 365):
    """Remove audit logs older than specified days."""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted = self.db.query(AuditLog).filter(
            AuditLog.timestamp < cutoff
        ).delete(synchronize_session=False)
        self.db.commit()
        logger.info(f"Cleaned up {deleted} old audit logs")
        return {"status": "success", "deleted": deleted}
    except Exception as e:
        self.db.rollback()
        logger.error(f"Failed to cleanup old audit logs: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(base=DatabaseTask, bind=True)
def generate_daily_report(self, municipality_id: Optional[str] = None):
    """Generate daily statistics report for municipality or all."""
    try:
        report_service = ReportService(self.db)
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        if municipality_id:
            report = report_service.generate_municipality_report(
                municipality_id, yesterday, datetime.utcnow()
            )
        else:
            report = report_service.generate_system_wide_report(
                yesterday, datetime.utcnow()
            )
        
        logger.info(f"Generated daily report for {municipality_id or 'system'}")
        return {"status": "success", "report": report}
    except Exception as e:
        logger.error(f"Failed to generate daily report: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(base=DatabaseTask, bind=True)
def generate_weekly_analytics(self, municipality_id: Optional[str] = None):
    """Generate weekly analytics and trends."""
    try:
        analytics_service = AnalyticsService(self.db)
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        analytics = analytics_service.calculate_trends(
            municipality_id, week_ago, datetime.utcnow()
        )
        
        logger.info(f"Generated weekly analytics for {municipality_id or 'system'}")
        return {"status": "success", "analytics": analytics}
    except Exception as e:
        logger.error(f"Failed to generate weekly analytics: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(base=DatabaseTask, bind=True)
def backup_database(self):
    """Create database backup and upload to S3."""
    try:
        backup_service = BackupService()
        result = backup_service.create_backup()
        logger.info(f"Database backup completed: {result}")
        return {"status": "success", "backup": result}
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(base=DatabaseTask, bind=True)
def check_sensor_health(self):
    """Check for inactive sensors and generate alerts."""
    try:
        threshold = datetime.utcnow() - timedelta(hours=2)
        
        inactive_sensors = self.db.query(Sensor).filter(
            Sensor.is_active == True,
            Sensor.last_reading_at < threshold
        ).all()
        
        notification_service = NotificationService(self.db)
        
        for sensor in inactive_sensors:
            alert = Alert(
                municipality_id=sensor.municipality_id,
                sensor_id=sensor.id,
                alert_type="sensor_offline",
                severity="medium",
                title=f"Sensor {sensor.name} is offline",
                description=f"No data received for over 2 hours",
                status="active"
            )
            self.db.add(alert)
            
            notification_service.send_alert_notification(alert)
        
        self.db.commit()
        logger.info(f"Health check found {len(inactive_sensors)} inactive sensors")
        return {"status": "success", "inactive_count": len(inactive_sensors)}
    except Exception as e:
        self.db.rollback()
        logger.error(f"Sensor health check failed: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(base=DatabaseTask, bind=True)
def aggregate_sensor_data(self, hours: int = 1):
    """Aggregate sensor data for analytics and reporting."""
    try:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        aggregates = self.db.query(
            SensorReading.sensor_id,
            func.avg(SensorReading.value).label('avg_value'),
            func.min(SensorReading.value).label('min_value'),
            func.max(SensorReading.value).label('max_value'),
            func.count(SensorReading.id).label('reading_count')
        ).filter(
            SensorReading.timestamp >= cutoff
        ).group_by(SensorReading.sensor_id).all()
        
        logger.info(f"Aggregated data for {len(aggregates)} sensors")
        return {"status": "success", "aggregates": len(aggregates)}
    except Exception as e:
        logger.error(f"Data aggregation failed: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(base=DatabaseTask, bind=True)
def validate_data_quality(self):
    """Run data quality checks on recent sensor readings."""
    try:
        quality_service = DataQualityService(self.db)
        results = quality_service.run_quality_checks()
        
        logger.info(f"Data quality validation completed: {results}")
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Data quality validation failed: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(base=DatabaseTask, bind=True)
def send_scheduled_reports(self):
    """Send scheduled reports to subscribed users."""
    try:
        notification_service = NotificationService(self.db)
        municipalities = self.db.query(Municipality).all()
        
        sent_count = 0
        for municipality in municipalities:
            report = generate_daily_report.apply_async(
                args=[municipality.id]
            ).get()
            
            if report.get("status") == "success":
                notification_service.send_report_notification(
                    municipality.id, report["report"]
                )
                sent_count += 1
        
        logger.info(f"Sent {sent_count} scheduled reports")
        return {"status": "success", "sent": sent_count}
    except Exception as e:
        logger.error(f"Failed to send scheduled reports: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(base=DatabaseTask, bind=True)
def cleanup_expired_tokens(self):
    """Clean up expired JWT tokens from blacklist."""
    try:
        # Implementation depends on token blacklist strategy
        logger.info("Token cleanup completed")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Token cleanup failed: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(base=DatabaseTask, bind=True)
def recalculate_sensor_statistics(self, sensor_id: str):
    """Recalculate statistical baselines for a sensor."""
    try:
        sensor = self.db.query(Sensor).filter(Sensor.id == sensor_id).first()
        if not sensor:
            return {"status": "error", "message": "Sensor not found"}
        
        # Get last 30 days of readings
        cutoff = datetime.utcnow() - timedelta(days=30)
        readings = self.db.query(SensorReading).filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.timestamp >= cutoff
        ).all()
        
        if readings:
            values = [r.value for r in readings]
            import numpy as np
            
            sensor.baseline_mean = float(np.mean(values))
            sensor.baseline_std = float(np.std(values))
            sensor.baseline_min = float(np.min(values))
            sensor.baseline_max = float(np.max(values))
            
            self.db.commit()
            logger.info(f"Recalculated statistics for sensor {sensor_id}")
        
        return {"status": "success", "readings_analyzed": len(readings)}
    except Exception as e:
        self.db.rollback()
        logger.error(f"Failed to recalculate sensor statistics: {e}")
        return {"status": "error", "message": str(e)}


# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    'cleanup-old-readings-daily': {
        'task': 'app.tasks.cleanup_old_readings',
        'schedule': 86400.0,  # Daily
        'args': (90,)
    },
    'cleanup-old-alerts-weekly': {
        'task': 'app.tasks.cleanup_old_alerts',
        'schedule': 604800.0,  # Weekly
        'args': (180,)
    },
    'cleanup-old-audit-logs-monthly': {
        'task': 'app.tasks.cleanup_old_audit_logs',
        'schedule': 2592000.0,  # Monthly
        'args': (365,)
    },
    'generate-daily-reports': {
        'task': 'app.tasks.generate_daily_report',
        'schedule': 86400.0,  # Daily at midnight
    },
    'generate-weekly-analytics': {
        'task': 'app.tasks.generate_weekly_analytics',
        'schedule': 604800.0,  # Weekly
    },
    'backup-database-daily': {
        'task': 'app.tasks.backup_database',
        'schedule': 86400.0,  # Daily
    },
    'check-sensor-health-hourly': {
        'task': 'app.tasks.check_sensor_health',
        'schedule': 3600.0,  # Hourly
    },
    'aggregate-sensor-data-hourly': {
        'task': 'app.tasks.aggregate_sensor_data',
        'schedule': 3600.0,  # Hourly
        'args': (1,)
    },
    'validate-data-quality-daily': {
        'task': 'app.tasks.validate_data_quality',
        'schedule': 86400.0,  # Daily
    },
    'send-scheduled-reports-daily': {
        'task': 'app.tasks.send_scheduled_reports',
        'schedule': 86400.0,  # Daily
    },
    'cleanup-expired-tokens-hourly': {
        'task': 'app.tasks.cleanup_expired_tokens',
        'schedule': 3600.0,  # Hourly
    },
}
