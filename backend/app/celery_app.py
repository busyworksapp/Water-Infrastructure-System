from celery import Celery
from .core.config import settings

celery_app = Celery(
    "water_monitoring",
    broker=settings.resolved_celery_broker_url,
    backend=settings.resolved_celery_result_backend
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery_app.task
def cleanup_old_readings():
    """Remove sensor readings older than 90 days"""
    from datetime import datetime, timedelta
    from .core.database import SessionLocal
    from .models.sensor import SensorReading
    
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=90)
        deleted = db.query(SensorReading).filter(SensorReading.timestamp < cutoff).delete()
        db.commit()
        return f"Deleted {deleted} old readings"
    finally:
        db.close()

@celery_app.task
def generate_daily_report(municipality_id: str):
    """Generate daily statistics report"""
    from .core.database import SessionLocal
    from .models.sensor import Sensor, SensorReading
    from .models.alert import Alert
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        total_readings = db.query(SensorReading).filter(
            SensorReading.timestamp >= yesterday
        ).count()
        
        anomalies = db.query(SensorReading).filter(
            SensorReading.timestamp >= yesterday,
            SensorReading.is_anomaly == True
        ).count()
        
        alerts = db.query(Alert).filter(
            Alert.municipality_id == municipality_id,
            Alert.created_at >= yesterday
        ).count()
        
        return {
            "date": yesterday.date().isoformat(),
            "total_readings": total_readings,
            "anomalies": anomalies,
            "alerts": alerts
        }
    finally:
        db.close()

celery_app.conf.beat_schedule = {
    'cleanup-old-readings': {
        'task': 'app.celery_app.cleanup_old_readings',
        'schedule': 86400.0,  # Daily
    },
}
