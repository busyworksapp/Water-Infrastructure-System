"""Batch processing service for bulk operations."""
from typing import List, Dict
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ..models.sensor import Sensor, SensorReading
from ..models.alert import Alert
from ..services.anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)

class BatchProcessor:
    """Handle bulk data operations efficiently."""
    
    def __init__(self, db: Session):
        self.db = db
        self.anomaly_detector = AnomalyDetector()
    
    def bulk_insert_readings(self, readings: List[Dict]) -> Dict:
        """Bulk insert sensor readings with validation."""
        success_count = 0
        error_count = 0
        errors = []
        
        try:
            reading_objects = []
            for data in readings:
                try:
                    reading = SensorReading(
                        sensor_id=data['sensor_id'],
                        timestamp=data.get('timestamp', datetime.utcnow()),
                        value=data['value'],
                        unit=data.get('unit', 'bar'),
                        quality_score=data.get('quality_score', 1.0),
                        battery_level=data.get('battery_level'),
                        signal_strength=data.get('signal_strength')
                    )
                    reading_objects.append(reading)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    errors.append({"data": data, "error": str(e)})
            
            self.db.bulk_save_objects(reading_objects)
            self.db.commit()
            
            return {
                "success": True,
                "inserted": success_count,
                "failed": error_count,
                "errors": errors[:10]  # Limit error list
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Bulk insert failed: {e}")
            return {"success": False, "error": str(e)}
    
    def bulk_update_sensors(self, updates: List[Dict]) -> Dict:
        """Bulk update sensor configurations."""
        updated = 0
        for update in updates:
            sensor = self.db.query(Sensor).filter(Sensor.id == update['sensor_id']).first()
            if sensor:
                for key, value in update.items():
                    if key != 'sensor_id' and hasattr(sensor, key):
                        setattr(sensor, key, value)
                updated += 1
        
        self.db.commit()
        return {"updated": updated, "total": len(updates)}
    
    def bulk_resolve_alerts(self, alert_ids: List[str], resolved_by: str) -> Dict:
        """Bulk resolve multiple alerts."""
        alerts = self.db.query(Alert).filter(Alert.id.in_(alert_ids)).all()
        for alert in alerts:
            alert.status = 'resolved'
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = resolved_by
        
        self.db.commit()
        return {"resolved": len(alerts)}
