"""
Predictive Maintenance Service
Analyzes sensor patterns to identify equipment degradation and maintenance needs
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging
import statistics

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)


class MaintenanceRisk(str, Enum):
    """Maintenance risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MaintenancePrediction:
    """Prediction for equipment maintenance"""
    
    def __init__(
        self,
        sensor_id: int,
        equipment_name: str,
        risk_level: MaintenanceRisk,
        predicted_failure_date: Optional[datetime],
        days_to_failure: Optional[int],
        indicators: List[str],
        recommendations: List[str],
        confidence: float = 0.0
    ):
        self.sensor_id = sensor_id
        self.equipment_name = equipment_name
        self.risk_level = risk_level
        self.predicted_failure_date = predicted_failure_date
        self.days_to_failure = days_to_failure
        self.indicators = indicators
        self.recommendations = recommendations
        self.confidence = confidence
        self.generated_at = datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "sensor_id": self.sensor_id,
            "equipment_name": self.equipment_name,
            "risk_level": self.risk_level,
            "predicted_failure_date": self.predicted_failure_date.isoformat() if self.predicted_failure_date else None,
            "days_to_failure": self.days_to_failure,
            "indicators": self.indicators,
            "recommendations": self.recommendations,
            "confidence": round(self.confidence, 2),
            "generated_at": self.generated_at.isoformat()
        }


class PredictiveMaintenanceService:
    """Service for predictive maintenance analysis"""

    @staticmethod
    def analyze_sensor_health(
        sensor_readings: List[Tuple[datetime, float]],
        sensor_id: int,
        equipment_name: str = "Sensor"
    ) -> MaintenancePrediction:
        """
        Analyze sensor readings for maintenance predictions
        
        Uses multiple indicators:
        1. Increasing trend in readings (degradation)
        2. Increased variance (instability)
        3. Frequency of out-of-range values
        4. Signal strength degradation
        """
        
        if not sensor_readings or len(sensor_readings) < 5:
            return MaintenancePrediction(
                sensor_id=sensor_id,
                equipment_name=equipment_name,
                risk_level=MaintenanceRisk.LOW,
                predicted_failure_date=None,
                days_to_failure=None,
                indicators=["Insufficient data"],
                recommendations=["Continue monitoring"],
                confidence=0.0
            )

        # Extract values and timestamps
        timestamps = [ts for ts, _ in sensor_readings]
        values = [v for _, v in sensor_readings]

        # Calculate indicators
        indicators = []
        risk_score = 0.0  # 0-100 scale
        confidence = 0.0

        # 1. Trend analysis
        trend_slope = PredictiveMaintenanceService._calculate_trend(values)
        if trend_slope > 0.1:  # Positive trend = degradation
            indicators.append(f"Increasing trend detected ({trend_slope:.3f} per measurement)")
            risk_score += 15
            confidence += 0.2

        # 2. Variance analysis
        if len(values) >= 2:
            variance = statistics.variance(values) if len(values) > 1 else 0
            recent_variance = statistics.variance(values[-10:]) if len(values) >= 10 else variance

            if recent_variance > variance * 1.5:
                indicators.append(f"Increased instability detected ({recent_variance:.2f})")
                risk_score += 20
                confidence += 0.25

        # 3. Out-of-range frequency
        mean_val = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0

        if std_dev > 0:
            out_of_range = sum(
                1 for v in values
                if abs(v - mean_val) > 3 * std_dev
            )
            out_of_range_pct = (out_of_range / len(values)) * 100

            if out_of_range_pct > 5:
                indicators.append(f"High out-of-range readings ({out_of_range_pct:.1f}%)")
                risk_score += 15
                confidence += 0.15

        # 4. Recent degradation
        if len(values) >= 20:
            recent_avg = statistics.mean(values[-10:])
            older_avg = statistics.mean(values[-20:-10])

            if recent_avg > older_avg * 1.1:  # 10% increase
                indicators.append(f"Recent degradation observed (+{((recent_avg / older_avg - 1) * 100):.1f}%)")
                risk_score += 25
                confidence += 0.2

        # 5. Variability pattern
        coefficient_of_variation = (std_dev / mean_val * 100) if mean_val != 0 else 0
        if coefficient_of_variation > 30:
            indicators.append(f"High variability ({coefficient_of_variation:.1f}%)")
            risk_score += 10
            confidence += 0.1

        # Determine risk level and predictions
        if risk_score < 20:
            risk_level = MaintenanceRisk.LOW
            days_to_failure = None
            predicted_date = None
        elif risk_score < 40:
            risk_level = MaintenanceRisk.MEDIUM
            days_to_failure = 30  # Estimated
            predicted_date = datetime.utcnow() + timedelta(days=30)
        elif risk_score < 60:
            risk_level = MaintenanceRisk.HIGH
            days_to_failure = 14  # Estimated
            predicted_date = datetime.utcnow() + timedelta(days=14)
        else:
            risk_level = MaintenanceRisk.CRITICAL
            days_to_failure = 7  # Estimated
            predicted_date = datetime.utcnow() + timedelta(days=7)

        # Generate recommendations
        recommendations = PredictiveMaintenanceService._get_recommendations(
            risk_level, indicators
        )

        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)

        return MaintenancePrediction(
            sensor_id=sensor_id,
            equipment_name=equipment_name,
            risk_level=risk_level,
            predicted_failure_date=predicted_date,
            days_to_failure=days_to_failure,
            indicators=indicators if indicators else ["No degradation detected"],
            recommendations=recommendations,
            confidence=confidence
        )

    @staticmethod
    def _calculate_trend(values: List[float]) -> float:
        """Calculate linear trend using least squares method"""
        
        if len(values) < 2:
            return 0.0

        n = len(values)
        x_values = list(range(n))
        
        # Calculate slope (b) in y = a + bx
        x_mean = sum(x_values) / n
        y_mean = sum(values) / n
        
        numerator = sum(
            (x_values[i] - x_mean) * (values[i] - y_mean)
            for i in range(n)
        )
        denominator = sum(
            (x_values[i] - x_mean) ** 2
            for i in range(n)
        )

        if denominator == 0:
            return 0.0

        return numerator / denominator

    @staticmethod
    def _get_recommendations(risk_level: MaintenanceRisk, indicators: List[str]) -> List[str]:
        """Generate maintenance recommendations based on risk level"""
        
        base_recommendations = {
            MaintenanceRisk.LOW: [
                "Continue regular monitoring",
                "No immediate action required",
                "Review readings monthly"
            ],
            MaintenanceRisk.MEDIUM: [
                "Schedule maintenance within 30 days",
                "Increase monitoring frequency to weekly",
                "Check for hardware issues",
                "Review calibration status"
            ],
            MaintenanceRisk.HIGH: [
                "Schedule maintenance within 14 days",
                "Increase monitoring to every 2 days",
                "Prepare replacement equipment",
                "Document current configuration",
                "Check power supply and connections"
            ],
            MaintenanceRisk.CRITICAL: [
                "Schedule emergency maintenance immediately",
                "Continuous monitoring required",
                "Have backup sensor ready",
                "Alert operations team",
                "Consider alternative data collection methods"
            ]
        }

        recommendations = base_recommendations.get(risk_level, [])

        # Add indicator-specific recommendations
        specific_recommendations = []

        for indicator in indicators:
            if "trend" in indicator.lower():
                specific_recommendations.append("Investigate cause of increasing trend")
            if "instability" in indicator.lower():
                specific_recommendations.append("Check sensor calibration and connections")
            if "out-of-range" in indicator.lower():
                specific_recommendations.append("Verify sensor configuration and range settings")
            if "degradation" in indicator.lower():
                specific_recommendations.append("Plan equipment replacement")
            if "variability" in indicator.lower():
                specific_recommendations.append("Check for environmental interference")

        return recommendations + specific_recommendations

    @staticmethod
    def predict_maintenance_schedule(
        sensor_readings_dict: Dict[int, List[Tuple[datetime, float]]],
        equipment_names: Dict[int, str]
    ) -> List[MaintenancePrediction]:
        """
        Predict maintenance for multiple sensors
        
        Args:
            sensor_readings_dict: Dict of sensor_id -> list of (timestamp, value) tuples
            equipment_names: Dict of sensor_id -> equipment name
        
        Returns:
            List of MaintenancePrediction objects
        """
        
        predictions = []

        for sensor_id, readings in sensor_readings_dict.items():
            equipment_name = equipment_names.get(sensor_id, f"Sensor {sensor_id}")
            
            prediction = PredictiveMaintenanceService.analyze_sensor_health(
                sensor_readings=readings,
                sensor_id=sensor_id,
                equipment_name=equipment_name
            )
            
            predictions.append(prediction)

        # Sort by risk level (critical first)
        risk_order = {
            MaintenanceRisk.CRITICAL: 0,
            MaintenanceRisk.HIGH: 1,
            MaintenanceRisk.MEDIUM: 2,
            MaintenanceRisk.LOW: 3
        }

        predictions.sort(
            key=lambda p: (risk_order.get(p.risk_level, 99), p.confidence),
            reverse=True
        )

        return predictions

    @staticmethod
    def get_maintenance_summary(
        predictions: List[MaintenancePrediction]
    ) -> Dict:
        """Generate summary from multiple predictions"""
        
        if not predictions:
            return {
                "total_sensors": 0,
                "healthy": 0,
                "needs_attention": 0,
                "critical": 0,
                "average_confidence": 0.0,
                "next_scheduled_maintenance": None
            }

        critical = sum(1 for p in predictions if p.risk_level == MaintenanceRisk.CRITICAL)
        high = sum(1 for p in predictions if p.risk_level == MaintenanceRisk.HIGH)
        medium = sum(1 for p in predictions if p.risk_level == MaintenanceRisk.MEDIUM)
        low = sum(1 for p in predictions if p.risk_level == MaintenanceRisk.LOW)

        # Find next scheduled maintenance
        urgent_dates = [
            p.predicted_failure_date for p in predictions
            if p.predicted_failure_date and p.risk_level in [MaintenanceRisk.HIGH, MaintenanceRisk.CRITICAL]
        ]
        next_maintenance = min(urgent_dates) if urgent_dates else None

        return {
            "total_sensors": len(predictions),
            "by_risk_level": {
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low
            },
            "needs_attention": critical + high,
            "average_confidence": round(
                sum(p.confidence for p in predictions) / len(predictions),
                2
            ) if predictions else 0.0,
            "next_scheduled_maintenance": next_maintenance.isoformat() if next_maintenance else None,
            "generated_at": datetime.utcnow().isoformat()
        }


# Global service instance
predictive_maintenance_service = PredictiveMaintenanceService()
