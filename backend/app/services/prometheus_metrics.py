"""Prometheus metrics exporter for water monitoring system."""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from typing import Dict
import time

from ..core.config import settings


class MetricsCollector:
    """Collect and expose Prometheus metrics."""
    
    def __init__(self):
        # HTTP metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint']
        )
        
        # Sensor metrics
        self.sensor_readings_total = Counter(
            'sensor_readings_total',
            'Total sensor readings received',
            ['sensor_id', 'protocol']
        )
        
        self.sensor_readings_anomalies = Counter(
            'sensor_readings_anomalies_total',
            'Total anomalous readings detected',
            ['sensor_id', 'detection_method']
        )
        
        self.active_sensors = Gauge(
            'active_sensors_total',
            'Number of active sensors',
            ['municipality_id']
        )
        
        # Alert metrics
        self.alerts_total = Counter(
            'alerts_total',
            'Total alerts generated',
            ['municipality_id', 'severity', 'alert_type']
        )
        
        self.active_alerts = Gauge(
            'active_alerts_total',
            'Number of active alerts',
            ['municipality_id', 'severity']
        )
        
        # WebSocket metrics
        self.websocket_connections = Gauge(
            'websocket_connections_active',
            'Number of active WebSocket connections',
            ['municipality_id']
        )
        
        # Database metrics
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration in seconds',
            ['query_type']
        )
        
        self.db_connections = Gauge(
            'db_connections_active',
            'Number of active database connections'
        )
        
        # MQTT metrics
        self.mqtt_messages_received = Counter(
            'mqtt_messages_received_total',
            'Total MQTT messages received',
            ['topic']
        )
        
        self.mqtt_messages_processed = Counter(
            'mqtt_messages_processed_total',
            'Total MQTT messages successfully processed',
            ['topic']
        )
        
        self.mqtt_messages_failed = Counter(
            'mqtt_messages_failed_total',
            'Total MQTT messages that failed processing',
            ['topic', 'error_type']
        )
        
        # Celery metrics
        self.celery_tasks_total = Counter(
            'celery_tasks_total',
            'Total Celery tasks executed',
            ['task_name', 'status']
        )
        
        self.celery_task_duration = Histogram(
            'celery_task_duration_seconds',
            'Celery task duration in seconds',
            ['task_name']
        )
        
        # System metrics
        self.system_uptime = Gauge(
            'system_uptime_seconds',
            'System uptime in seconds'
        )
        
        self.data_quality_score = Gauge(
            'data_quality_score',
            'Overall data quality score',
            ['municipality_id']
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            'cache_hits_total',
            'Total cache hits',
            ['cache_type']
        )
        
        self.cache_misses = Counter(
            'cache_misses_total',
            'Total cache misses',
            ['cache_type']
        )
        
        # IoT Protocol metrics
        self.iot_protocol_messages = Counter(
            'iot_protocol_messages_total',
            'Total IoT protocol messages',
            ['protocol', 'status']
        )
        
        self.start_time = time.time()
    
    def record_http_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics."""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        self.http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_sensor_reading(self, sensor_id: str, protocol: str):
        """Record sensor reading received."""
        self.sensor_readings_total.labels(
            sensor_id=sensor_id,
            protocol=protocol
        ).inc()
    
    def record_anomaly(self, sensor_id: str, detection_method: str):
        """Record anomaly detection."""
        self.sensor_readings_anomalies.labels(
            sensor_id=sensor_id,
            detection_method=detection_method
        ).inc()
    
    def update_active_sensors(self, municipality_id: str, count: int):
        """Update active sensor count."""
        self.active_sensors.labels(municipality_id=municipality_id).set(count)
    
    def record_alert(self, municipality_id: str, severity: str, alert_type: str):
        """Record alert generation."""
        self.alerts_total.labels(
            municipality_id=municipality_id,
            severity=severity,
            alert_type=alert_type
        ).inc()
    
    def update_active_alerts(self, municipality_id: str, severity: str, count: int):
        """Update active alert count."""
        self.active_alerts.labels(
            municipality_id=municipality_id,
            severity=severity
        ).set(count)
    
    def update_websocket_connections(self, municipality_id: str, count: int):
        """Update WebSocket connection count."""
        self.websocket_connections.labels(municipality_id=municipality_id).set(count)
    
    def record_db_query(self, query_type: str, duration: float):
        """Record database query metrics."""
        self.db_query_duration.labels(query_type=query_type).observe(duration)
    
    def update_db_connections(self, count: int):
        """Update database connection count."""
        self.db_connections.set(count)
    
    def record_mqtt_message(self, topic: str, success: bool, error_type: str = None):
        """Record MQTT message metrics."""
        self.mqtt_messages_received.labels(topic=topic).inc()
        
        if success:
            self.mqtt_messages_processed.labels(topic=topic).inc()
        else:
            self.mqtt_messages_failed.labels(
                topic=topic,
                error_type=error_type or "unknown"
            ).inc()
    
    def record_celery_task(self, task_name: str, status: str, duration: float):
        """Record Celery task metrics."""
        self.celery_tasks_total.labels(
            task_name=task_name,
            status=status
        ).inc()
        
        self.celery_task_duration.labels(task_name=task_name).observe(duration)
    
    def update_system_uptime(self):
        """Update system uptime."""
        uptime = time.time() - self.start_time
        self.system_uptime.set(uptime)
    
    def update_data_quality(self, municipality_id: str, score: float):
        """Update data quality score."""
        self.data_quality_score.labels(municipality_id=municipality_id).set(score)
    
    def record_cache_access(self, cache_type: str, hit: bool):
        """Record cache access."""
        if hit:
            self.cache_hits.labels(cache_type=cache_type).inc()
        else:
            self.cache_misses.labels(cache_type=cache_type).inc()
    
    def record_iot_protocol_message(self, protocol: str, status: str):
        """Record IoT protocol message."""
        self.iot_protocol_messages.labels(
            protocol=protocol,
            status=status
        ).inc()
    
    def get_metrics(self) -> Response:
        """Get Prometheus metrics in exposition format."""
        self.update_system_uptime()
        
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST
        )


# Global metrics collector instance
metrics_collector = MetricsCollector()


def get_metrics_endpoint():
    """FastAPI endpoint for Prometheus metrics."""
    return metrics_collector.get_metrics()
