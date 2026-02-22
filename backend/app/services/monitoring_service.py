from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Dict
import psutil
import logging

logger = logging.getLogger(__name__)

class MonitoringService:
    def get_system_health(self, db: Session) -> Dict:
        """Get comprehensive system health metrics"""
        try:
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "components": {
                    "database": self._check_database(db),
                    "system": self._check_system_resources(),
                    "sensors": self._check_sensor_health(db),
                    "alerts": self._check_alert_status(db)
                }
            }
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def _check_database(self, db: Session) -> Dict:
        """Check database connectivity and performance"""
        try:
            db.execute(text("SELECT 1"))
            return {"status": "healthy", "connected": True}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def _check_system_resources(self) -> Dict:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy" if cpu_percent < 80 and memory.percent < 80 else "warning",
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent
            }
        except Exception as e:
            return {"status": "unknown", "error": str(e)}
    
    def _check_sensor_health(self, db: Session) -> Dict:
        """Check sensor connectivity"""
        try:
            from ..models.sensor import Sensor, SensorStatus
            
            total = db.query(Sensor).count()
            active = db.query(Sensor).filter(Sensor.status == SensorStatus.ACTIVE).count()
            
            cutoff = datetime.utcnow() - timedelta(hours=1)
            recent_readings = db.query(Sensor).filter(
                Sensor.last_reading_at >= cutoff
            ).count()
            
            health_score = (recent_readings / total * 100) if total > 0 else 0
            
            return {
                "status": "healthy" if health_score > 80 else "warning",
                "total_sensors": total,
                "active_sensors": active,
                "recent_readings": recent_readings,
                "health_score": round(health_score, 2)
            }
        except Exception as e:
            return {"status": "unknown", "error": str(e)}
    
    def _check_alert_status(self, db: Session) -> Dict:
        """Check alert processing status"""
        try:
            from ..models.alert import Alert, AlertSeverity, AlertStatus
            
            open_alerts = db.query(Alert).filter(Alert.status == AlertStatus.OPEN).count()
            critical_alerts = db.query(Alert).filter(
                Alert.status == AlertStatus.OPEN,
                Alert.severity == AlertSeverity.CRITICAL
            ).count()
            
            return {
                "status": "warning" if critical_alerts > 0 else "healthy",
                "open_alerts": open_alerts,
                "critical_alerts": critical_alerts
            }
        except Exception as e:
            return {"status": "unknown", "error": str(e)}
    
    def get_performance_metrics(self) -> Dict:
        """Get performance metrics"""
        try:
            return {
                "cpu": {
                    "percent": psutil.cpu_percent(interval=1),
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "used": psutil.disk_usage('/').used,
                    "percent": psutil.disk_usage('/').percent
                }
            }
        except Exception as e:
            logger.error(f"Performance metrics error: {e}")
            return {}

monitoring_service = MonitoringService()
