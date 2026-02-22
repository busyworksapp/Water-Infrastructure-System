from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import csv
import io
import json
from ..models.sensor import Sensor, SensorReading
from ..models.alert import Alert
from ..models.municipality import Municipality

class ExportService:
    def export_sensor_readings_csv(
        self,
        db: Session,
        sensor_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """Export sensor readings to CSV"""
        readings = db.query(SensorReading).filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.timestamp >= start_date,
            SensorReading.timestamp <= end_date
        ).order_by(SensorReading.timestamp).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Timestamp', 'Value', 'Unit', 'Is Anomaly', 'Quality Score'])
        
        # Data
        for reading in readings:
            writer.writerow([
                reading.timestamp.isoformat(),
                reading.value,
                reading.unit,
                reading.is_anomaly,
                reading.quality_score
            ])
        
        return output.getvalue()
    
    def export_alerts_csv(
        self,
        db: Session,
        municipality_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """Export alerts to CSV"""
        alerts = db.query(Alert).filter(
            Alert.municipality_id == municipality_id,
            Alert.created_at >= start_date,
            Alert.created_at <= end_date
        ).order_by(Alert.created_at.desc()).all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Alert ID', 'Title', 'Type', 'Severity', 'Status',
            'Created At', 'Resolved At', 'Description'
        ])
        
        # Data
        for alert in alerts:
            writer.writerow([
                alert.id,
                alert.title,
                alert.alert_type.value,
                alert.severity.value,
                alert.status.value,
                alert.created_at.isoformat(),
                alert.resolved_at.isoformat() if alert.resolved_at else '',
                alert.description
            ])
        
        return output.getvalue()
    
    def export_municipality_report_json(
        self,
        db: Session,
        municipality_id: str,
        days: int = 30
    ) -> dict:
        """Export comprehensive municipality report"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        municipality = db.query(Municipality).filter(
            Municipality.id == municipality_id
        ).first()
        
        if not municipality:
            return {"error": "Municipality not found"}
        
        # Sensor statistics
        sensors = db.query(Sensor).filter(
            Sensor.municipality_id == municipality_id
        ).all()
        
        total_sensors = len(sensors)
        active_sensors = sum(1 for s in sensors if s.status.value == 'active')
        
        # Reading statistics
        total_readings = db.query(SensorReading).join(Sensor).filter(
            Sensor.municipality_id == municipality_id,
            SensorReading.timestamp >= cutoff
        ).count()
        
        anomalous_readings = db.query(SensorReading).join(Sensor).filter(
            Sensor.municipality_id == municipality_id,
            SensorReading.timestamp >= cutoff,
            SensorReading.is_anomaly == True
        ).count()
        
        # Alert statistics
        alerts = db.query(Alert).filter(
            Alert.municipality_id == municipality_id,
            Alert.created_at >= cutoff
        ).all()
        
        alert_by_severity = {}
        for alert in alerts:
            severity = alert.severity.value
            alert_by_severity[severity] = alert_by_severity.get(severity, 0) + 1
        
        return {
            "municipality": {
                "id": municipality.id,
                "name": municipality.name,
                "code": municipality.code
            },
            "report_period": {
                "start": cutoff.isoformat(),
                "end": datetime.utcnow().isoformat(),
                "days": days
            },
            "sensors": {
                "total": total_sensors,
                "active": active_sensors,
                "inactive": total_sensors - active_sensors
            },
            "readings": {
                "total": total_readings,
                "anomalous": anomalous_readings,
                "anomaly_rate": round(anomalous_readings / total_readings * 100, 2) if total_readings > 0 else 0
            },
            "alerts": {
                "total": len(alerts),
                "by_severity": alert_by_severity,
                "open": sum(1 for a in alerts if a.status.value == 'open'),
                "resolved": sum(1 for a in alerts if a.status.value == 'resolved')
            },
            "generated_at": datetime.utcnow().isoformat()
        }

export_service = ExportService()
