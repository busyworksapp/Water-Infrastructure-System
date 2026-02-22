"""
Real-Time Analytics Aggregation Service
Provides hourly, daily, and monthly data summaries with caching
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)


class AggregationGranularity(str, Enum):
    """Aggregation time granularities"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class AggregationMetric(str, Enum):
    """Metrics to aggregate"""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    STDDEV = "stddev"


class TimeSeriesDataPoint:
    """Individual data point in time series"""
    
    def __init__(
        self,
        timestamp: datetime,
        value: float,
        metrics: Optional[Dict[str, float]] = None
    ):
        self.timestamp = timestamp
        self.value = value
        self.metrics = metrics or {}

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "metrics": self.metrics
        }


class AggregatedData:
    """Container for aggregated analytics"""
    
    def __init__(
        self,
        sensor_id: int,
        granularity: AggregationGranularity,
        start_time: datetime,
        end_time: datetime
    ):
        self.sensor_id = sensor_id
        self.granularity = granularity
        self.start_time = start_time
        self.end_time = end_time
        self.data_points: List[TimeSeriesDataPoint] = []
        self.summary_stats: Dict[str, float] = {}
        self.generated_at = datetime.utcnow()

    def add_data_point(self, point: TimeSeriesDataPoint):
        """Add data point to aggregation"""
        self.data_points.append(point)

    def calculate_summary(self):
        """Calculate summary statistics"""
        
        if not self.data_points:
            return

        values = [p.value for p in self.data_points]

        self.summary_stats = {
            "total_points": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values) if values else 0,
            "min": min(values) if values else 0,
            "max": max(values) if values else 0,
            "stddev": self._calculate_stddev(values),
            "median": self._calculate_median(values),
            "p95": self._calculate_percentile(values, 0.95),
            "p99": self._calculate_percentile(values, 0.99),
        }

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "sensor_id": self.sensor_id,
            "granularity": self.granularity,
            "period": {
                "start": self.start_time.isoformat(),
                "end": self.end_time.isoformat()
            },
            "data_points": [p.to_dict() for p in self.data_points],
            "summary": self.summary_stats,
            "generated_at": self.generated_at.isoformat()
        }

    @staticmethod
    def _calculate_stddev(values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    @staticmethod
    def _calculate_median(values: List[float]) -> float:
        """Calculate median"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n % 2 == 0:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        else:
            return sorted_values[n // 2]

    @staticmethod
    def _calculate_percentile(values: List[float], percentile: float) -> float:
        """Calculate percentile (0-1)"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]


class RealTimeAnalyticsService:
    """Service for real-time analytics aggregation"""

    # Cache key patterns
    CACHE_KEY_HOURLY = "analytics:hourly:{sensor_id}:{timestamp}"
    CACHE_KEY_DAILY = "analytics:daily:{sensor_id}:{date}"
    CACHE_KEY_MONTHLY = "analytics:monthly:{sensor_id}:{year_month}"
    CACHE_EXPIRY_HOURLY = 3600  # 1 hour
    CACHE_EXPIRY_DAILY = 86400  # 1 day
    CACHE_EXPIRY_MONTHLY = 2592000  # 30 days

    @staticmethod
    def aggregate_sensor_data(
        readings: List[Tuple[datetime, float]],
        sensor_id: int,
        granularity: AggregationGranularity = AggregationGranularity.HOURLY
    ) -> AggregatedData:
        """
        Aggregate sensor readings into time buckets
        
        Args:
            readings: List of (timestamp, value) tuples
            sensor_id: Sensor ID
            granularity: Time granularity for aggregation
        
        Returns:
            AggregatedData with bucketed and summarized data
        """
        
        if not readings:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            aggregated = AggregatedData(sensor_id, granularity, start_time, end_time)
            aggregated.calculate_summary()
            return aggregated

        # Sort by timestamp
        sorted_readings = sorted(readings, key=lambda x: x[0])
        start_time = sorted_readings[0][0]
        end_time = sorted_readings[-1][0]

        aggregated = AggregatedData(sensor_id, granularity, start_time, end_time)

        # Group readings by granularity
        buckets = RealTimeAnalyticsService._create_buckets(
            start_time, end_time, granularity
        )

        for bucket_start, bucket_end in buckets:
            bucket_readings = [
                v for ts, v in sorted_readings
                if bucket_start <= ts < bucket_end
            ]

            if bucket_readings:
                avg_value = sum(bucket_readings) / len(bucket_readings)
                point = TimeSeriesDataPoint(
                    timestamp=bucket_start,
                    value=avg_value,
                    metrics={
                        "count": len(bucket_readings),
                        "sum": sum(bucket_readings),
                        "min": min(bucket_readings),
                        "max": max(bucket_readings),
                        "stddev": RealTimeAnalyticsService._stddev(bucket_readings)
                    }
                )
                aggregated.add_data_point(point)

        aggregated.calculate_summary()
        return aggregated

    @staticmethod
    def _create_buckets(
        start: datetime,
        end: datetime,
        granularity: AggregationGranularity
    ) -> List[Tuple[datetime, datetime]]:
        """Create time buckets for aggregation"""
        
        buckets = []
        current = start

        if granularity == AggregationGranularity.HOURLY:
            delta = timedelta(hours=1)
        elif granularity == AggregationGranularity.DAILY:
            delta = timedelta(days=1)
            current = current.replace(hour=0, minute=0, second=0, microsecond=0)
        elif granularity == AggregationGranularity.WEEKLY:
            delta = timedelta(weeks=1)
            current = current.replace(hour=0, minute=0, second=0, microsecond=0)
        elif granularity == AggregationGranularity.MONTHLY:
            # Handle month boundaries
            if current.month == 12:
                next_month = current.replace(year=current.year + 1, month=1, day=1)
            else:
                next_month = current.replace(month=current.month + 1, day=1)
            delta = next_month - current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            current = current.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            delta = timedelta(days=1)

        while current < end:
            next_bucket = current + delta
            buckets.append((current, next_bucket))
            current = next_bucket

        return buckets

    @staticmethod
    def _stddev(values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    @staticmethod
    def calculate_moving_average(
        readings: List[Tuple[datetime, float]],
        window_size: int = 10
    ) -> List[TimeSeriesDataPoint]:
        """Calculate moving average"""
        
        if len(readings) < window_size:
            return [
                TimeSeriesDataPoint(ts, val)
                for ts, val in readings
            ]

        result = []
        for i in range(len(readings)):
            start_idx = max(0, i - window_size + 1)
            window_values = [readings[j][1] for j in range(start_idx, i + 1)]
            moving_avg = sum(window_values) / len(window_values)
            
            result.append(TimeSeriesDataPoint(readings[i][0], moving_avg))

        return result

    @staticmethod
    def detect_trends(
        aggregated_data: AggregatedData,
        min_points: int = 3
    ) -> Dict[str, any]:
        """
        Detect trends in aggregated data
        """
        
        if len(aggregated_data.data_points) < min_points:
            return {
                "trend": "insufficient_data",
                "slope": 0.0,
                "confidence": 0.0,
                "direction": "unknown"
            }

        values = [p.value for p in aggregated_data.data_points]
        
        # Calculate trend using linear regression
        n = len(values)
        x = list(range(n))
        
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum(
            (x[i] - x_mean) * (values[i] - y_mean)
            for i in range(n)
        )
        denominator = sum(
            (x[i] - x_mean) ** 2
            for i in range(n)
        )

        slope = numerator / denominator if denominator != 0 else 0.0

        # Calculate R-squared for confidence
        ss_res = sum((values[i] - (slope * x[i] + (y_mean - slope * x_mean))) ** 2 for i in range(n))
        ss_tot = sum((values[i] - y_mean) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0

        direction = "increasing" if slope > 0.001 else "decreasing" if slope < -0.001 else "stable"

        return {
            "trend": "detected" if abs(slope) > 0.001 else "stable",
            "slope": round(slope, 4),
            "confidence": round(r_squared, 2),
            "direction": direction,
            "change_per_period": round(slope * n, 2)
        }

    @staticmethod
    def compare_periods(
        current_data: AggregatedData,
        previous_data: AggregatedData
    ) -> Dict[str, any]:
        """
        Compare analytics between two time periods
        """
        
        if not current_data.summary_stats or not previous_data.summary_stats:
            return {"error": "Insufficient data for comparison"}

        current_avg = current_data.summary_stats.get("avg", 0)
        previous_avg = previous_data.summary_stats.get("avg", 0)

        if previous_avg == 0:
            pct_change = 0
        else:
            pct_change = ((current_avg - previous_avg) / previous_avg) * 100

        return {
            "current_avg": round(current_avg, 2),
            "previous_avg": round(previous_avg, 2),
            "difference": round(current_avg - previous_avg, 2),
            "pct_change": round(pct_change, 2),
            "trend": "improving" if pct_change < 0 else "declining" if pct_change > 0 else "stable",
            "current_min": current_data.summary_stats.get("min", 0),
            "current_max": current_data.summary_stats.get("max", 0),
            "previous_min": previous_data.summary_stats.get("min", 0),
            "previous_max": previous_data.summary_stats.get("max", 0)
        }

    @staticmethod
    def generate_analytics_report(
        sensor_id: int,
        aggregated_data: AggregatedData,
        trends: Optional[Dict] = None,
        comparisons: Optional[List[Dict]] = None
    ) -> Dict:
        """Generate comprehensive analytics report"""
        
        report = {
            "sensor_id": sensor_id,
            "period": {
                "start": aggregated_data.start_time.isoformat(),
                "end": aggregated_data.end_time.isoformat(),
                "granularity": aggregated_data.granularity
            },
            "summary": aggregated_data.summary_stats,
            "trends": trends or {},
            "comparisons": comparisons or [],
            "data_points_count": len(aggregated_data.data_points),
            "generated_at": datetime.utcnow().isoformat(),
            "insights": RealTimeAnalyticsService._generate_insights(aggregated_data)
        }

        return report

    @staticmethod
    def _generate_insights(data: AggregatedData) -> List[str]:
        """Generate human-readable insights from data"""
        
        insights = []
        stats = data.summary_stats

        if not stats:
            return ["Insufficient data for insights"]

        # Variability insight
        if stats.get("stddev", 0) > stats.get("avg", 0) * 0.5:
            insights.append("High variability detected in readings")

        # Extreme values
        min_val = stats.get("min", 0)
        max_val = stats.get("max", 0)
        avg_val = stats.get("avg", 0)

        if max_val > avg_val * 1.5:
            insights.append(f"Peak readings {((max_val / avg_val - 1) * 100):.0f}% above average")

        if min_val < avg_val * 0.5:
            insights.append(f"Low readings {((1 - min_val / avg_val) * 100):.0f}% below average")

        # Percentile insights
        p95 = stats.get("p95", 0)
        p99 = stats.get("p99", 0)

        if p99 > p95 * 1.2:
            insights.append("Outliers detected at tail of distribution")

        return insights if insights else ["Normal operation"]


# Global analytics service instance
analytics_service = RealTimeAnalyticsService()
