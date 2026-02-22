"""Task scheduler for automated jobs"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.backup_service import backup_service
from app.services.ml_detector import ml_detector
import logging

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """Start the scheduler"""
        # Daily backup at 2 AM
        self.scheduler.add_job(
            self.daily_backup,
            CronTrigger(hour=2, minute=0),
            id='daily_backup',
            name='Daily Backup'
        )
        
        # Retrain ML models weekly on Sunday at 3 AM
        self.scheduler.add_job(
            self.retrain_ml_models,
            CronTrigger(day_of_week='sun', hour=3, minute=0),
            id='retrain_ml',
            name='Retrain ML Models'
        )
        
        # Cleanup old data monthly on 1st at 4 AM
        self.scheduler.add_job(
            self.cleanup_old_data,
            CronTrigger(day=1, hour=4, minute=0),
            id='cleanup_data',
            name='Cleanup Old Data'
        )
        
        self.scheduler.start()
        logger.info("Scheduler started with 3 jobs")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    async def daily_backup(self):
        """Perform daily backup"""
        try:
            db = SessionLocal()
            backup_service.backup_sensor_readings(db, days=7)
            backup_service.backup_alerts(db, days=30)
            db.close()
            logger.info("Daily backup completed")
        except Exception as e:
            logger.error(f"Backup failed: {e}")
    
    async def retrain_ml_models(self):
        """Retrain ML models with latest data"""
        try:
            db = SessionLocal()
            from app.models.sensor import Sensor
            sensors = db.query(Sensor).filter(Sensor.is_active == True).all()
            
            for sensor in sensors:
                ml_detector.train(db, sensor.id)
            
            db.close()
            logger.info(f"Retrained ML models for {len(sensors)} sensors")
        except Exception as e:
            logger.error(f"ML retraining failed: {e}")
    
    async def cleanup_old_data(self):
        """Cleanup data older than 90 days"""
        try:
            from datetime import datetime, timedelta
            from app.models.sensor import SensorReading
            
            db = SessionLocal()
            cutoff = datetime.utcnow() - timedelta(days=90)
            
            deleted = db.query(SensorReading).filter(
                SensorReading.timestamp < cutoff
            ).delete()
            
            db.commit()
            db.close()
            logger.info(f"Cleaned up {deleted} old readings")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

scheduler_service = SchedulerService()
