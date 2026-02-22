from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import Dict, List
import numpy as np
from ..models.sensor import Sensor, SensorReading

class PredictiveMaintenanceService:
    def __init__(self):
        self.failure_threshold = 0.7
    
    def predict_failure_risk(self, db: Session, sensor: Sensor) -> Dict:
        """Predict sensor failure risk based on historical patterns"""
        try:
            # Get recent readings
            cutoff = datetime.utcnow() - timedelta(days=7)
            readings = db.query(SensorReading).filter(
                SensorReading.sensor_id == sensor.id,
                SensorReading.timestamp >= cutoff
            ).order_by(SensorReading.timestamp).all()
            
            if len(readings) < 50:
                return {"risk_level": "unknown", "score": 0.0, "reason": "Insufficient data"}
            
            # Calculate risk factors
            battery_risk = self._calculate_battery_risk(sensor)
            quality_risk = self._calculate_quality_risk(readings)
            anomaly_risk = self._calculate_anomaly_risk(readings)
            communication_risk = self._calculate_communication_risk(sensor)
            
            # Weighted average
            total_risk = (
                battery_risk * 0.3 +
                quality_risk * 0.25 +
                anomaly_risk * 0.25 +
                communication_risk * 0.2
            )
            
            risk_level = self._get_risk_level(total_risk)
            
            return {
                "risk_level": risk_level,
                "score": round(total_risk, 2),
                "factors": {
                    "battery": round(battery_risk, 2),
                    "quality": round(quality_risk, 2),
                    "anomaly": round(anomaly_risk, 2),
                    "communication": round(communication_risk, 2)
                },
                "recommendation": self._get_recommendation(risk_level)
            }
            
        except Exception as e:
            return {"risk_level": "error", "score": 0.0, "reason": str(e)}
    
    def _calculate_battery_risk(self, sensor: Sensor) -> float:
        """Calculate risk based on battery level"""
        if not sensor.battery_level:
            return 0.0
        
        if sensor.battery_level < 20:
            return 1.0
        elif sensor.battery_level < 40:
            return 0.7
        elif sensor.battery_level < 60:
            return 0.4
        else:
            return 0.1
    
    def _calculate_quality_risk(self, readings: List[SensorReading]) -> float:
        """Calculate risk based on data quality"""
        quality_scores = [r.quality_score for r in readings if r.quality_score]
        
        if not quality_scores:
            return 0.0
        
        avg_quality = np.mean(quality_scores)
        
        if avg_quality < 0.7:
            return 1.0
        elif avg_quality < 0.85:
            return 0.6
        elif avg_quality < 0.95:
            return 0.3
        else:
            return 0.1
    
    def _calculate_anomaly_risk(self, readings: List[SensorReading]) -> float:
        """Calculate risk based on anomaly frequency"""
        anomaly_count = sum(1 for r in readings if r.is_anomaly)
        anomaly_rate = anomaly_count / len(readings)
        
        if anomaly_rate > 0.3:
            return 1.0
        elif anomaly_rate > 0.15:
            return 0.7
        elif anomaly_rate > 0.05:
            return 0.4
        else:
            return 0.1
    
    def _calculate_communication_risk(self, sensor: Sensor) -> float:
        """Calculate risk based on communication reliability"""
        if not sensor.last_reading_at:
            return 1.0
        
        time_since_last = (datetime.utcnow() - sensor.last_reading_at).total_seconds()
        expected_interval = sensor.sampling_interval_sec or 60
        
        if time_since_last > expected_interval * 10:
            return 1.0
        elif time_since_last > expected_interval * 5:
            return 0.7
        elif time_since_last > expected_interval * 2:
            return 0.4
        else:
            return 0.1
    
    def _get_risk_level(self, score: float) -> str:
        """Convert risk score to level"""
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        elif score >= 0.2:
            return "low"
        else:
            return "minimal"
    
    def _get_recommendation(self, risk_level: str) -> str:
        """Get maintenance recommendation"""
        recommendations = {
            "critical": "Immediate maintenance required. Sensor may fail soon.",
            "high": "Schedule maintenance within 24 hours.",
            "medium": "Schedule maintenance within 1 week.",
            "low": "Monitor closely. Maintenance recommended within 1 month.",
            "minimal": "Sensor operating normally. Continue regular monitoring."
        }
        return recommendations.get(risk_level, "No recommendation available")
