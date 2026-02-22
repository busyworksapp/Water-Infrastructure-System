"""Data quality and validation service"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.sensor import SensorReading, Sensor
import logging

logger = logging.getLogger(__name__)

class DataQualityService:
    
    def validate_reading(self, sensor: Sensor, value: float):
        """Validate sensor reading against expected ranges"""
        issues = []
        
        # Check if value is within sensor type range
        if sensor.sensor_type:
            if sensor.sensor_type.min_value and value < sensor.sensor_type.min_value:
                issues.append(f"Value below minimum ({sensor.sensor_type.min_value})")
            if sensor.sensor_type.max_value and value > sensor.sensor_type.max_value:
                issues.append(f"Value above maximum ({sensor.sensor_type.max_value})")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "quality_score": 1.0 if len(issues) == 0 else 0.5
        }
    
    def detect_duplicates(self, db: Session, sensor_id: int, hours: int = 24):
        """Find duplicate readings"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        from sqlalchemy import func
        duplicates = db.query(
            SensorReading.timestamp,
            SensorReading.value,
            func.count(SensorReading.id).label('count')
        ).filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.timestamp >= cutoff
        ).group_by(
            SensorReading.timestamp,
            SensorReading.value
        ).having(func.count(SensorReading.id) > 1).all()
        
        return [{
            "timestamp": d.timestamp.isoformat(),
            "value": float(d.value),
            "count": d.count
        } for d in duplicates]
    
    def detect_gaps(self, db: Session, sensor_id: int, hours: int = 24, expected_interval_min: int = 5):
        """Detect missing data gaps"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        readings = db.query(SensorReading).filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.timestamp >= cutoff
        ).order_by(SensorReading.timestamp).all()
        
        gaps = []
        for i in range(1, len(readings)):
            time_diff = (readings[i].timestamp - readings[i-1].timestamp).total_seconds() / 60
            if time_diff > expected_interval_min * 2:
                gaps.append({
                    "start": readings[i-1].timestamp.isoformat(),
                    "end": readings[i].timestamp.isoformat(),
                    "duration_minutes": int(time_diff)
                })
        
        return gaps
    
    def calculate_completeness(self, db: Session, sensor_id: int, hours: int = 24, expected_interval_min: int = 5):
        """Calculate data completeness percentage"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        actual_count = db.query(func.count(SensorReading.id)).filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.timestamp >= cutoff
        ).scalar()
        
        expected_count = (hours * 60) / expected_interval_min
        completeness = min((actual_count / expected_count) * 100, 100) if expected_count > 0 else 0
        
        return {
            "sensor_id": sensor_id,
            "hours": hours,
            "actual_readings": actual_count,
            "expected_readings": int(expected_count),
            "completeness_percent": round(completeness, 2)
        }
    
    def get_quality_report(self, db: Session, sensor_id: int, hours: int = 24):
        """Generate comprehensive quality report"""
        duplicates = self.detect_duplicates(db, sensor_id, hours)
        gaps = self.detect_gaps(db, sensor_id, hours)
        completeness = self.calculate_completeness(db, sensor_id, hours)
        
        return {
            "sensor_id": sensor_id,
            "period_hours": hours,
            "completeness": completeness,
            "duplicates_found": len(duplicates),
            "gaps_found": len(gaps),
            "quality_score": self._calculate_overall_score(completeness, duplicates, gaps)
        }
    
    def _calculate_overall_score(self, completeness, duplicates, gaps):
        """Calculate overall quality score"""
        score = completeness['completeness_percent']
        score -= len(duplicates) * 2  # Penalty for duplicates
        score -= len(gaps) * 5  # Penalty for gaps
        return max(0, min(100, score))

data_quality_service = DataQualityService()
