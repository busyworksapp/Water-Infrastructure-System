"""Comprehensive system health monitoring and diagnostics."""
from typing import Dict, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import psutil
import logging

from ..core.database import engine
from ..models.sensor import Sensor, SensorReading
from ..models.alert import Alert
from ..models.user import User
from ..models.municipality import Municipality

logger = logging.getLogger(__name__)


class SystemHealthMonitor:
    """Monitor overall system health and performance."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_comprehensive_health(self) -> Dict:
        """Get comprehensive system health report."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": self._calculate_overall_status(),
            "components": {
                "database": self._check_database_health(),
                "sensors": self._check_sensor_health(),
                "alerts": self._check_alert_health(),
                "data_ingestion": self._check_ingestion_health(),
                "system_resources": self._check_system_resources()
            },
            "metrics": self._get_key_metrics(),
            "recommendations": self._generate_recommendations()
        }
    
    def _check_database_health(self) -> Dict:
        """Check database connectivity and performance."""
        try:
            # Test connection
            start = datetime.utcnow()
            self.db.execute("SELECT 1")
            query_time = (datetime.utcnow() - start).total_seconds() * 1000
            
            # Get database size
            if 'postgresql' in str(engine.url):
                size_query = "SELECT pg_database_size(current_database())"
            else:
                size_query = "SELECT SUM(data_length + index_length) FROM information_schema.tables"
            
            db_size = self.db.execute(size_query).scalar() or 0
            
            # Get connection count
            active_connections = len(engine.pool.checkedout())
            pool_size = engine.pool.size()
            
            status = "healthy" if query_time < 100 else "degraded" if query_time < 500 else "unhealthy"
            
            return {
                "status": status,
                "query_time_ms": round(query_time, 2),
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "active_connections": active_connections,
                "pool_size": pool_size,
                "connection_utilization": round((active_connections / pool_size * 100), 1) if pool_size > 0 else 0
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def _check_sensor_health(self) -> Dict:
        """Check sensor network health."""
        try:
            total_sensors = self.db.query(func.count(Sensor.id)).scalar()
            active_sensors = self.db.query(func.count(Sensor.id)).filter(
                Sensor.is_active == True
            ).scalar()
            
            # Sensors with recent data (last hour)
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            reporting_sensors = self.db.query(func.count(Sensor.id)).filter(
                Sensor.last_reading_at >= recent_cutoff
            ).scalar()
            
            # Sensors with low battery
            low_battery = self.db.query(func.count(Sensor.id)).filter(
                Sensor.battery_level < 20,
                Sensor.battery_level.isnot(None)
            ).scalar()
            
            reporting_rate = (reporting_sensors / active_sensors * 100) if active_sensors > 0 else 0
            
            status = "healthy" if reporting_rate > 90 else "degraded" if reporting_rate > 70 else "unhealthy"
            
            return {
                "status": status,
                "total_sensors": total_sensors,
                "active_sensors": active_sensors,
                "reporting_sensors": reporting_sensors,
                "reporting_rate": round(reporting_rate, 1),
                "low_battery_sensors": low_battery,
                "offline_sensors": active_sensors - reporting_sensors
            }
        except Exception as e:
            logger.error(f"Sensor health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def _check_alert_health(self) -> Dict:
        """Check alert system health."""
        try:
            # Active alerts
            active_alerts = self.db.query(func.count(Alert.id)).filter(
                Alert.status == 'active'
            ).scalar()
            
            # Critical alerts
            critical_alerts = self.db.query(func.count(Alert.id)).filter(
                Alert.status == 'active',
                Alert.severity == 'critical'
            ).scalar()
            
            # Alerts in last 24 hours
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_alerts = self.db.query(func.count(Alert.id)).filter(
                Alert.created_at >= recent_cutoff
            ).scalar()
            
            # Average resolution time
            resolved_alerts = self.db.query(Alert).filter(
                Alert.resolved_at.isnot(None),
                Alert.resolved_at >= recent_cutoff
            ).all()
            
            if resolved_alerts:
                resolution_times = [
                    (a.resolved_at - a.created_at).total_seconds() / 60
                    for a in resolved_alerts
                ]
                avg_resolution_time = sum(resolution_times) / len(resolution_times)
            else:
                avg_resolution_time = 0
            
            status = "healthy" if critical_alerts == 0 else "degraded" if critical_alerts < 5 else "unhealthy"
            
            return {
                "status": status,
                "active_alerts": active_alerts,
                "critical_alerts": critical_alerts,
                "alerts_last_24h": recent_alerts,
                "avg_resolution_time_minutes": round(avg_resolution_time, 1)
            }
        except Exception as e:
            logger.error(f"Alert health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def _check_ingestion_health(self) -> Dict:
        """Check data ingestion health."""
        try:
            # Readings in last hour
            hour_ago = datetime.utcnow() - timedelta(hours=1)
            readings_last_hour = self.db.query(func.count(SensorReading.id)).filter(
                SensorReading.timestamp >= hour_ago
            ).scalar()
            
            # Readings in last 5 minutes
            five_min_ago = datetime.utcnow() - timedelta(minutes=5)
            readings_last_5min = self.db.query(func.count(SensorReading.id)).filter(
                SensorReading.timestamp >= five_min_ago
            ).scalar()
            
            # Calculate ingestion rate
            ingestion_rate = readings_last_hour / 60  # per minute
            
            # Anomaly rate
            anomalies = self.db.query(func.count(SensorReading.id)).filter(
                SensorReading.timestamp >= hour_ago,
                SensorReading.is_anomaly == True
            ).scalar()
            
            anomaly_rate = (anomalies / readings_last_hour * 100) if readings_last_hour > 0 else 0
            
            status = "healthy" if readings_last_5min > 0 else "degraded" if readings_last_hour > 0 else "unhealthy"
            
            return {
                "status": status,
                "readings_last_hour": readings_last_hour,
                "readings_last_5min": readings_last_5min,
                "ingestion_rate_per_minute": round(ingestion_rate, 1),
                "anomaly_rate": round(anomaly_rate, 2)
            }
        except Exception as e:
            logger.error(f"Ingestion health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def _check_system_resources(self) -> Dict:
        """Check system resource utilization."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            status = "healthy"
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = "unhealthy"
            elif cpu_percent > 70 or memory.percent > 70 or disk.percent > 80:
                status = "degraded"
            
            return {
                "status": status,
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory.percent, 1),
                "memory_available_mb": round(memory.available / (1024 * 1024), 1),
                "disk_percent": round(disk.percent, 1),
                "disk_free_gb": round(disk.free / (1024 * 1024 * 1024), 1)
            }
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def _get_key_metrics(self) -> Dict:
        """Get key system metrics."""
        try:
            total_municipalities = self.db.query(func.count(Municipality.id)).scalar()
            total_users = self.db.query(func.count(User.id)).scalar()
            active_users = self.db.query(func.count(User.id)).filter(
                User.is_active == True
            ).scalar()
            
            # Total readings
            total_readings = self.db.query(func.count(SensorReading.id)).scalar()
            
            # Data growth (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_readings = self.db.query(func.count(SensorReading.id)).filter(
                SensorReading.timestamp >= week_ago
            ).scalar()
            
            return {
                "total_municipalities": total_municipalities,
                "total_users": total_users,
                "active_users": active_users,
                "total_readings": total_readings,
                "readings_last_7_days": recent_readings,
                "avg_readings_per_day": round(recent_readings / 7, 0)
            }
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")
            return {}
    
    def _calculate_overall_status(self) -> str:
        """Calculate overall system status."""
        try:
            components = [
                self._check_database_health(),
                self._check_sensor_health(),
                self._check_alert_health(),
                self._check_ingestion_health(),
                self._check_system_resources()
            ]
            
            statuses = [c.get("status", "unknown") for c in components]
            
            if "unhealthy" in statuses or "error" in statuses:
                return "unhealthy"
            elif "degraded" in statuses:
                return "degraded"
            else:
                return "healthy"
        except:
            return "unknown"
    
    def _generate_recommendations(self) -> List[str]:
        """Generate system recommendations based on health checks."""
        recommendations = []
        
        try:
            # Check database
            db_health = self._check_database_health()
            if db_health.get("connection_utilization", 0) > 80:
                recommendations.append("Consider increasing database connection pool size")
            
            # Check sensors
            sensor_health = self._check_sensor_health()
            if sensor_health.get("reporting_rate", 100) < 80:
                recommendations.append("Multiple sensors offline - check network connectivity")
            if sensor_health.get("low_battery_sensors", 0) > 0:
                recommendations.append(f"{sensor_health['low_battery_sensors']} sensors have low battery")
            
            # Check alerts
            alert_health = self._check_alert_health()
            if alert_health.get("critical_alerts", 0) > 0:
                recommendations.append(f"{alert_health['critical_alerts']} critical alerts require immediate attention")
            
            # Check resources
            resource_health = self._check_system_resources()
            if resource_health.get("cpu_percent", 0) > 80:
                recommendations.append("High CPU usage - consider scaling resources")
            if resource_health.get("memory_percent", 0) > 80:
                recommendations.append("High memory usage - consider increasing RAM")
            if resource_health.get("disk_percent", 0) > 80:
                recommendations.append("Disk space running low - cleanup or expand storage")
            
            if not recommendations:
                recommendations.append("System operating normally - no immediate actions required")
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            recommendations.append("Unable to generate recommendations")
        
        return recommendations


def get_system_health_monitor(db: Session) -> SystemHealthMonitor:
    """Factory function to get system health monitor."""
    return SystemHealthMonitor(db)
