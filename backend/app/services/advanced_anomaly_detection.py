"""
Advanced Anomaly Detection Service
Uses statistical methods (Z-score, isolation forest concepts) to identify anomalies
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging
import statistics
import math

logger = logging.getLogger(__name__)


class AnomalySeverity(str, Enum):
    """Anomaly severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(str, Enum):
    """Types of anomalies detected"""
    OUTLIER = "outlier"  # Statistical outlier
    TREND = "trend"  # Unusual trend
    SEASONALITY = "seasonality"  # Unexpected seasonal change
    VOLATILITY = "volatility"  # Unusual variance
    PATTERN_BREAK = "pattern_break"  # Break in expected pattern
    THRESHOLD_BREACH = "threshold_breach"  # Exceeds configured thresholds


class AnomalyDetection:
    """Detected anomaly"""
    
    def __init__(
        self,
        sensor_id: int,
        anomaly_type: AnomalyType,
        severity: AnomalySeverity,
        value: float,
        expected_range: Tuple[float, float],
        z_score: Optional[float] = None,
        description: str = "",
        timestamp: Optional[datetime] = None,
        context: Optional[Dict] = None
    ):
        self.sensor_id = sensor_id
        self.anomaly_type = anomaly_type
        self.severity = severity
        self.value = value
        self.expected_range = expected_range
        self.z_score = z_score
        self.description = description
        self.timestamp = timestamp or datetime.utcnow()
        self.context = context or {}
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "sensor_id": self.sensor_id,
            "anomaly_type": self.anomaly_type,
            "severity": self.severity,
            "value": self.value,
            "expected_range": {
                "min": self.expected_range[0],
                "max": self.expected_range[1]
            },
            "z_score": self.z_score,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "created_at": self.created_at.isoformat()
        }


class AdvancedAnomalyDetectionService:
    """Service for detecting anomalies in sensor data"""

    # Configuration
    Z_SCORE_THRESHOLD_LOW = 2.0  # Mild anomalies
    Z_SCORE_THRESHOLD_MEDIUM = 2.5  # Moderate anomalies
    Z_SCORE_THRESHOLD_HIGH = 3.0  # Significant anomalies
    Z_SCORE_THRESHOLD_CRITICAL = 3.5  # Critical anomalies

    @staticmethod
    def detect_outliers_zscore(
        values: List[float],
        sensor_id: int,
        threshold: float = 2.5
    ) -> List[AnomalyDetection]:
        """
        Detect outliers using Z-score method
        
        Z-score = (value - mean) / std_dev
        Values with |z-score| > threshold are outliers
        """
        
        if len(values) < 3:
            return []

        anomalies = []
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)

        if std_dev == 0:
            return []

        for i, value in enumerate(values):
            z_score = (value - mean) / std_dev

            if abs(z_score) > threshold:
                # Determine severity based on z-score magnitude
                if abs(z_score) >= 3.5:
                    severity = AnomalySeverity.CRITICAL
                elif abs(z_score) >= 3.0:
                    severity = AnomalySeverity.HIGH
                elif abs(z_score) >= 2.5:
                    severity = AnomalySeverity.MEDIUM
                else:
                    severity = AnomalySeverity.LOW

                anomalies.append(AnomalyDetection(
                    sensor_id=sensor_id,
                    anomaly_type=AnomalyType.OUTLIER,
                    severity=severity,
                    value=value,
                    expected_range=(mean - 2 * std_dev, mean + 2 * std_dev),
                    z_score=z_score,
                    description=f"Statistical outlier detected (Z-score: {z_score:.2f})"
                ))

        return anomalies

    @staticmethod
    def detect_trend_anomalies(
        values: List[float],
        sensor_id: int,
        window_size: int = 10
    ) -> List[AnomalyDetection]:
        """
        Detect unusual trends in data
        
        Compares recent trend with historical trend
        """
        
        if len(values) < window_size * 2:
            return []

        anomalies = []

        # Calculate historical trend
        historical_trend = AdvancedAnomalyDetectionService._calculate_trend(
            values[:-window_size]
        )

        # Calculate recent trend
        recent_trend = AdvancedAnomalyDetectionService._calculate_trend(
            values[-window_size:]
        )

        # Compare trends
        trend_change = recent_trend - historical_trend
        trend_change_pct = abs(trend_change) / (abs(historical_trend) + 0.001) * 100

        if trend_change_pct > 150:  # 150% change in trend
            severity = AnomalySeverity.HIGH
        elif trend_change_pct > 100:  # 100% change
            severity = AnomalySeverity.MEDIUM
        elif trend_change_pct > 50:  # 50% change
            severity = AnomalySeverity.LOW
        else:
            severity = None

        if severity:
            anomalies.append(AnomalyDetection(
                sensor_id=sensor_id,
                anomaly_type=AnomalyType.TREND,
                severity=severity,
                value=recent_trend,
                expected_range=(historical_trend - 0.5, historical_trend + 0.5),
                description=f"Trend change detected ({trend_change_pct:.1f}% deviation)",
                context={
                    "historical_trend": historical_trend,
                    "recent_trend": recent_trend,
                    "trend_change_pct": trend_change_pct
                }
            ))

        return anomalies

    @staticmethod
    def detect_volatility_anomalies(
        values: List[float],
        sensor_id: int,
        window_size: int = 10
    ) -> List[AnomalyDetection]:
        """
        Detect unusual volatility/variance in data
        
        Compares recent variance with historical variance
        """
        
        if len(values) < window_size * 2:
            return []

        anomalies = []

        # Calculate historical variance
        historical_variance = statistics.variance(values[:-window_size]) if len(values[:-window_size]) > 1 else 0

        # Calculate recent variance
        recent_variance = statistics.variance(values[-window_size:]) if len(values[-window_size:]) > 1 else 0

        # Compare variances
        if historical_variance > 0:
            variance_ratio = recent_variance / historical_variance
        else:
            variance_ratio = 0 if recent_variance == 0 else float('inf')

        if variance_ratio > 3:  # 3x increase
            severity = AnomalySeverity.HIGH
        elif variance_ratio > 2:  # 2x increase
            severity = AnomalySeverity.MEDIUM
        elif variance_ratio > 1.5:  # 1.5x increase
            severity = AnomalySeverity.LOW
        else:
            severity = None

        if severity:
            anomalies.append(AnomalyDetection(
                sensor_id=sensor_id,
                anomaly_type=AnomalyType.VOLATILITY,
                severity=severity,
                value=recent_variance,
                expected_range=(0, historical_variance * 1.5),
                description=f"Volatility increase detected ({variance_ratio:.2f}x historical)",
                context={
                    "historical_variance": historical_variance,
                    "recent_variance": recent_variance,
                    "variance_ratio": variance_ratio
                }
            ))

        return anomalies

    @staticmethod
    def detect_threshold_breaches(
        values: List[float],
        sensor_id: int,
        min_threshold: float,
        max_threshold: float
    ) -> List[AnomalyDetection]:
        """
        Detect values that exceed configured thresholds
        """
        
        anomalies = []

        for value in values:
            if value < min_threshold:
                severity = AnomalySeverity.HIGH if value < min_threshold * 0.5 else AnomalySeverity.MEDIUM
                anomalies.append(AnomalyDetection(
                    sensor_id=sensor_id,
                    anomaly_type=AnomalyType.THRESHOLD_BREACH,
                    severity=severity,
                    value=value,
                    expected_range=(min_threshold, max_threshold),
                    description=f"Value below minimum threshold ({value} < {min_threshold})"
                ))

            elif value > max_threshold:
                severity = AnomalySeverity.HIGH if value > max_threshold * 1.5 else AnomalySeverity.MEDIUM
                anomalies.append(AnomalyDetection(
                    sensor_id=sensor_id,
                    anomaly_type=AnomalyType.THRESHOLD_BREACH,
                    severity=severity,
                    value=value,
                    expected_range=(min_threshold, max_threshold),
                    description=f"Value above maximum threshold ({value} > {max_threshold})"
                ))

        return anomalies

    @staticmethod
    def detect_pattern_breaks(
        values: List[float],
        sensor_id: int,
        window_size: int = 20
    ) -> List[AnomalyDetection]:
        """
        Detect breaks in expected patterns (periodic behavior)
        
        Uses autocorrelation concept to identify periodic patterns
        """
        
        if len(values) < window_size:
            return []

        anomalies = []

        # Calculate repeating pattern (simple autocorrelation for period detection)
        for period in range(2, min(window_size // 2, 10)):
            pattern_distances = []

            for i in range(period, min(len(values), window_size)):
                if i - period >= 0:
                    distance = abs(values[i] - values[i - period])
                    pattern_distances.append(distance)

            if pattern_distances:
                avg_distance = statistics.mean(pattern_distances)
                std_dist = statistics.stdev(pattern_distances) if len(pattern_distances) > 1 else 0

                # Check if recent values break the pattern
                recent_distances = pattern_distances[-5:]
                recent_avg = statistics.mean(recent_distances)

                if recent_avg > avg_distance + 2 * std_dist:
                    anomalies.append(AnomalyDetection(
                        sensor_id=sensor_id,
                        anomaly_type=AnomalyType.PATTERN_BREAK,
                        severity=AnomalySeverity.MEDIUM,
                        value=recent_avg,
                        expected_range=(avg_distance - std_dist, avg_distance + std_dist),
                        description=f"Pattern break detected (period: {period})",
                        context={
                            "period": period,
                            "expected_distance": avg_distance,
                            "observed_distance": recent_avg
                        }
                    ))
                    break  # Only report the most significant pattern break

        return anomalies

    @staticmethod
    def comprehensive_anomaly_detection(
        values: List[float],
        sensor_id: int,
        min_threshold: Optional[float] = None,
        max_threshold: Optional[float] = None
    ) -> List[AnomalyDetection]:
        """
        Run all anomaly detection methods
        """
        
        all_anomalies = []

        # Z-score outlier detection
        all_anomalies.extend(
            AdvancedAnomalyDetectionService.detect_outliers_zscore(values, sensor_id)
        )

        # Trend anomalies
        all_anomalies.extend(
            AdvancedAnomalyDetectionService.detect_trend_anomalies(values, sensor_id)
        )

        # Volatility anomalies
        all_anomalies.extend(
            AdvancedAnomalyDetectionService.detect_volatility_anomalies(values, sensor_id)
        )

        # Threshold breaches
        if min_threshold is not None and max_threshold is not None:
            all_anomalies.extend(
                AdvancedAnomalyDetectionService.detect_threshold_breaches(
                    values, sensor_id, min_threshold, max_threshold
                )
            )

        # Pattern breaks
        if len(values) >= 40:
            all_anomalies.extend(
                AdvancedAnomalyDetectionService.detect_pattern_breaks(values, sensor_id)
            )

        # Remove duplicates (same anomaly type at same time)
        unique_anomalies = []
        seen = set()

        for anomaly in all_anomalies:
            key = (anomaly.sensor_id, anomaly.anomaly_type, anomaly.severity)
            if key not in seen:
                unique_anomalies.append(anomaly)
                seen.add(key)

        # Sort by severity (critical first)
        severity_order = {
            AnomalySeverity.CRITICAL: 0,
            AnomalySeverity.HIGH: 1,
            AnomalySeverity.MEDIUM: 2,
            AnomalySeverity.LOW: 3
        }

        unique_anomalies.sort(
            key=lambda x: severity_order.get(x.severity, 99)
        )

        return unique_anomalies

    @staticmethod
    def _calculate_trend(values: List[float]) -> float:
        """Calculate linear trend using least squares"""
        
        if len(values) < 2:
            return 0.0

        n = len(values)
        x_values = list(range(n))
        
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

        return numerator / denominator if denominator != 0 else 0.0

    @staticmethod
    def get_anomaly_summary(
        anomalies: List[AnomalyDetection]
    ) -> Dict:
        """Get summary of detected anomalies"""
        
        if not anomalies:
            return {
                "total_anomalies": 0,
                "by_severity": {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                },
                "by_type": {},
                "sensors_affected": [],
                "requires_action": False
            }

        critical = sum(1 for a in anomalies if a.severity == AnomalySeverity.CRITICAL)
        high = sum(1 for a in anomalies if a.severity == AnomalySeverity.HIGH)
        medium = sum(1 for a in anomalies if a.severity == AnomalySeverity.MEDIUM)
        low = sum(1 for a in anomalies if a.severity == AnomalySeverity.LOW)

        # Count by type
        by_type = {}
        for anomaly in anomalies:
            atype = anomaly.anomaly_type
            by_type[atype] = by_type.get(atype, 0) + 1

        # Sensors affected
        sensors_affected = list(set(a.sensor_id for a in anomalies))

        return {
            "total_anomalies": len(anomalies),
            "by_severity": {
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low
            },
            "by_type": by_type,
            "sensors_affected": sensors_affected,
            "requires_action": critical > 0 or high > 0
        }


# Global service instance
anomaly_detection_service = AdvancedAnomalyDetectionService()
