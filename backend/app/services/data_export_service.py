"""Data export service for compliance and reporting."""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import csv
import json
import io

from ..models.sensor import Sensor, SensorReading
from ..models.alert import Alert, Incident
from ..models.maintenance import MaintenanceLog

class DataExportService:
    """Export system data in various formats."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def export_sensor_readings(
        self,
        sensor_id: str,
        start_date: datetime,
        end_date: datetime,
        format: str = "csv"
    ) -> bytes:
        """Export sensor readings for date range."""
        readings = self.db.query(SensorReading).filter(
            and_(
                SensorReading.sensor_id == sensor_id,
                SensorReading.timestamp >= start_date,
                SensorReading.timestamp <= end_date
            )
        ).order_by(SensorReading.timestamp).all()
        
        if format == "csv":
            return self._to_csv(readings, [
                "timestamp", "value", "unit", "quality_score",
                "is_anomaly", "battery_level", "signal_strength"
            ])
        elif format == "json":
            return self._to_json([{
                "timestamp": r.timestamp.isoformat(),
                "value": r.value,
                "unit": r.unit,
                "quality_score": r.quality_score,
                "is_anomaly": r.is_anomaly,
                "battery_level": r.battery_level,
                "signal_strength": r.signal_strength
            } for r in readings])
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def export_alerts(
        self,
        municipality_id: str,
        start_date: datetime,
        end_date: datetime,
        format: str = "csv"
    ) -> bytes:
        """Export alerts for municipality."""
        alerts = self.db.query(Alert).filter(
            and_(
                Alert.municipality_id == municipality_id,
                Alert.created_at >= start_date,
                Alert.created_at <= end_date
            )
        ).order_by(Alert.created_at.desc()).all()
        
        if format == "csv":
            return self._to_csv(alerts, [
                "id", "alert_type", "severity", "status",
                "created_at", "resolved_at", "description"
            ])
        elif format == "json":
            return self._to_json([{
                "id": a.id,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "status": a.status,
                "created_at": a.created_at.isoformat(),
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
                "description": a.description
            } for a in alerts])
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def export_maintenance_logs(
        self,
        municipality_id: str,
        start_date: datetime,
        end_date: datetime,
        format: str = "csv"
    ) -> bytes:
        """Export maintenance logs."""
        logs = self.db.query(MaintenanceLog).join(Sensor).filter(
            and_(
                Sensor.municipality_id == municipality_id,
                MaintenanceLog.created_at >= start_date,
                MaintenanceLog.created_at <= end_date
            )
        ).order_by(MaintenanceLog.created_at.desc()).all()
        
        if format == "csv":
            return self._to_csv(logs, [
                "id", "sensor_id", "maintenance_type", "status",
                "scheduled_date", "completed_date", "notes", "cost"
            ])
        elif format == "json":
            return self._to_json([{
                "id": log.id,
                "sensor_id": log.sensor_id,
                "maintenance_type": log.maintenance_type,
                "status": log.status,
                "scheduled_date": log.scheduled_date.isoformat() if log.scheduled_date else None,
                "completed_date": log.completed_date.isoformat() if log.completed_date else None,
                "notes": log.notes,
                "cost": float(log.cost) if log.cost else None
            } for log in logs])
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def export_compliance_report(
        self,
        municipality_id: str,
        month: int,
        year: int
    ) -> bytes:
        """Generate monthly compliance report."""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # Gather statistics
        total_sensors = self.db.query(Sensor).filter(
            Sensor.municipality_id == municipality_id
        ).count()
        
        total_readings = self.db.query(SensorReading).join(Sensor).filter(
            and_(
                Sensor.municipality_id == municipality_id,
                SensorReading.timestamp >= start_date,
                SensorReading.timestamp < end_date
            )
        ).count()
        
        total_alerts = self.db.query(Alert).filter(
            and_(
                Alert.municipality_id == municipality_id,
                Alert.created_at >= start_date,
                Alert.created_at < end_date
            )
        ).count()
        
        critical_alerts = self.db.query(Alert).filter(
            and_(
                Alert.municipality_id == municipality_id,
                Alert.severity == "critical",
                Alert.created_at >= start_date,
                Alert.created_at < end_date
            )
        ).count()
        
        report = {
            "municipality_id": municipality_id,
            "period": f"{year}-{month:02d}",
            "generated_at": datetime.utcnow().isoformat(),
            "statistics": {
                "total_sensors": total_sensors,
                "total_readings": total_readings,
                "total_alerts": total_alerts,
                "critical_alerts": critical_alerts,
                "avg_readings_per_sensor": round(total_readings / total_sensors, 2) if total_sensors > 0 else 0
            }
        }
        
        return self._to_json(report)
    
    def _to_csv(self, data: List, fields: List[str]) -> bytes:
        """Convert data to CSV format."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        
        for item in data:
            row = {}
            for field in fields:
                value = getattr(item, field, None)
                if isinstance(value, datetime):
                    value = value.isoformat()
                row[field] = value
            writer.writerow(row)
        
        return output.getvalue().encode('utf-8')
    
    def _to_json(self, data) -> bytes:
        """Convert data to JSON format."""
        return json.dumps(data, indent=2, default=str).encode('utf-8')
