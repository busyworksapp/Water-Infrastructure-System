"""
Prometheus metrics service for system monitoring and observability.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import SessionLocal
from ..models.sensor import Sensor, SensorReading
from ..models.alert import Alert
from ..models.audit import AuditLog

logger = logging.getLogger(__name__)

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0)
)

# Database metrics
db_connection_pool_size = Gauge(
    'db_connection_pool_size',
    'Database connection pool size'
)

db_active_connections = Gauge(
    'db_active_connections',
    'Active database connections'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query latency',
    ['query_type'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0)
)

# Sensor metrics
sensors_total = Gauge(
    'sensors_total',
    'Total number of sensors',
    ['municipality', 'status']
)

sensor_readings_total = Counter(
    'sensor_readings_total',
    'Total sensor readings ingested',
    ['sensor_type', 'protocol']
)

sensor_reading_latency = Histogram(
    'sensor_reading_latency_seconds',
    'Sensor reading ingestion latency',
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0)
)

# Alert metrics
alerts_total = Counter(
    'alerts_total',
    'Total alerts generated',
    ['type', 'severity', 'municipality']
)

active_alerts_gauge = Gauge(
    'active_alerts_total',
    'Currently active alerts',
    ['severity']
)

alert_processing_duration = Histogram(
    'alert_processing_duration_seconds',
    'Alert processing latency',
    buckets=(0.01, 0.05, 0.1, 0.5)
)

# Anomaly detection metrics
anomalies_detected_total = Counter(
    'anomalies_detected_total',
    'Total anomalies detected',
    ['detection_method', 'sensor_type']
)

anomaly_score_histogram = Histogram(
    'anomaly_score',
    'Anomaly score distribution',
    buckets=(0.1, 0.3, 0.5, 0.7, 0.9)
)

# System health metrics
system_health_status = Gauge(
    'system_health_status',
    'System health status (1=healthy, 0=unhealthy)',
    ['component']
)

system_uptime_seconds = Gauge(
    'system_uptime_seconds',
    'System uptime in seconds'
)

# Cache metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['key_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['key_type']
)

# Background job metrics
background_jobs_total = Counter(
    'background_jobs_total',
    'Total background jobs processed',
    ['job_type', 'status']
)

background_job_duration = Histogram(
    'background_job_duration_seconds',
    'Background job execution time',
    ['job_type'],
    buckets=(1, 5, 10, 30, 60)
)


class MetricsService:
    """Service for managing system metrics and Prometheus integration."""

    def __init__(self):
        self.start_time = datetime.utcnow()

    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_seconds: float
    ):
        """Record HTTP request metrics."""
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status_code
        ).inc()
        
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration_seconds)

    def record_sensor_reading(
        self,
        sensor_type: str,
        protocol: str,
        duration_seconds: float,
        anomaly_score: float = 0.0
    ):
        """Record sensor reading metrics."""
        sensor_readings_total.labels(
            sensor_type=sensor_type,
            protocol=protocol
        ).inc()
        
        sensor_reading_latency.observe(duration_seconds)
        
        if anomaly_score > 0.5:
            anomaly_score_histogram.observe(anomaly_score)

    def record_alert(
        self,
        alert_type: str,
        severity: str,
        municipality_id: str,
        duration_seconds: float
    ):
        """Record alert generation metrics."""
        alerts_total.labels(
            type=alert_type,
            severity=severity,
            municipality=municipality_id
        ).inc()
        
        alert_processing_duration.observe(duration_seconds)

    def record_anomaly_detection(
        self,
        detection_method: str,
        sensor_type: str
    ):
        """Record anomaly detection metrics."""
        anomalies_detected_total.labels(
            detection_method=detection_method,
            sensor_type=sensor_type
        ).inc()

    def record_cache_operation(self, key_type: str, hit: bool):
        """Record cache hit/miss metrics."""
        if hit:
            cache_hits_total.labels(key_type=key_type).inc()
        else:
            cache_misses_total.labels(key_type=key_type).inc()

    def record_background_job(
        self,
        job_type: str,
        status: str,
        duration_seconds: float
    ):
        """Record background job metrics."""
        background_jobs_total.labels(
            job_type=job_type,
            status=status
        ).inc()
        
        background_job_duration.labels(job_type=job_type).observe(duration_seconds)

    def update_system_health(self, component: str, healthy: bool):
        """Update system health status for a component."""
        system_health_status.labels(component=component).set(1 if healthy else 0)

    def update_uptime(self):
        """Update system uptime metric."""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        system_uptime_seconds.set(uptime)

    def collect_database_metrics(self, db: Optional[Session] = None):
        """Collect database-related metrics."""
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False
        
        try:
            # Count sensors by status
            sensors_query = db.query(Sensor).all()
            active_count = sum(1 for s in sensors_query if s.is_active)
            inactive_count = len(sensors_query) - active_count
            
            sensors_total.labels(municipality="all", status="active").set(active_count)
            sensors_total.labels(municipality="all", status="inactive").set(inactive_count)
            
            # Count active alerts by severity
            active_alerts = db.query(Alert).filter(Alert.status == "open").all()
            for severity in ["critical", "high", "medium", "low", "info"]:
                count = sum(1 for a in active_alerts if a.severity.value == severity)
                active_alerts_gauge.labels(severity=severity).set(count)
        
        except Exception as e:
            logger.error(f"Failed to collect database metrics: {e}")
        finally:
            if should_close:
                db.close()

    def get_metrics_summary(self, db: Optional[Session] = None) -> Dict:
        """Get a summary of current metrics."""
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            readings_24h = db.query(SensorReading).filter(
                SensorReading.created_at >= cutoff_time
            ).count()
            
            alerts_24h = db.query(Alert).filter(
                Alert.created_at >= cutoff_time
            ).count()
            
            anomalies_24h = db.query(SensorReading).filter(
                SensorReading.is_anomaly.is_(True),
                SensorReading.created_at >= cutoff_time
            ).count()
            
            active_sensors = db.query(Sensor).filter(
                Sensor.is_active.is_(True)
            ).count()
            
            active_alerts = db.query(Alert).filter(
                Alert.status.in_(["open", "acknowledged"])
            ).count()
            
            return {
                "readings_24h": readings_24h,
                "alerts_24h": alerts_24h,
                "anomalies_24h": anomalies_24h,
                "active_sensors": active_sensors,
                "active_alerts": active_alerts,
                "system_uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            if should_close:
                db.close()

    def export_metrics(self) -> bytes:
        """Export metrics in Prometheus format."""
        return generate_latest()


# Global instance
metrics_service = MetricsService()
