"""Advanced geospatial analysis for pipeline monitoring and leak detection."""
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from geoalchemy2.functions import ST_Distance, ST_DWithin, ST_Buffer, ST_Intersects
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
import logging

from ..models.pipeline import Pipeline
from ..models.sensor import Sensor, SensorReading
from ..models.alert import Alert
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


class GeospatialAnalysisService:
    """Advanced geospatial analysis for water infrastructure."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def detect_pipeline_leaks(
        self, 
        pipeline_id: str, 
        time_window_hours: int = 24
    ) -> Dict:
        """
        Detect potential leaks by analyzing pressure/flow patterns along pipeline.
        Uses spatial correlation of sensor readings.
        """
        pipeline = self.db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
        if not pipeline:
            return {"status": "error", "message": "Pipeline not found"}
        
        # Get sensors along pipeline
        sensors = self.db.query(Sensor).filter(
            Sensor.pipeline_id == pipeline_id,
            Sensor.is_active == True
        ).all()
        
        if len(sensors) < 2:
            return {"status": "insufficient_sensors", "message": "Need at least 2 sensors"}
        
        cutoff = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        # Analyze pressure drops between consecutive sensors
        leak_candidates = []
        
        for i in range(len(sensors) - 1):
            sensor_a = sensors[i]
            sensor_b = sensors[i + 1]
            
            # Get recent readings
            readings_a = self.db.query(SensorReading).filter(
                SensorReading.sensor_id == sensor_a.id,
                SensorReading.timestamp >= cutoff
            ).order_by(SensorReading.timestamp.desc()).limit(100).all()
            
            readings_b = self.db.query(SensorReading).filter(
                SensorReading.sensor_id == sensor_b.id,
                SensorReading.timestamp >= cutoff
            ).order_by(SensorReading.timestamp.desc()).limit(100).all()
            
            if not readings_a or not readings_b:
                continue
            
            # Calculate average pressure difference
            if HAS_NUMPY:
                avg_a = np.mean([r.value for r in readings_a])
                avg_b = np.mean([r.value for r in readings_b])
            else:
                avg_a = sum(r.value for r in readings_a) / len(readings_a)
                avg_b = sum(r.value for r in readings_b) / len(readings_b)
            pressure_drop = avg_a - avg_b
            
            # Expected pressure drop based on distance and flow
            distance_km = self._calculate_distance(sensor_a, sensor_b)
            expected_drop = self._calculate_expected_pressure_drop(
                distance_km, pipeline.diameter, pipeline.material
            )
            
            # Anomalous pressure drop indicates potential leak
            if pressure_drop > expected_drop * 1.5:
                leak_probability = min((pressure_drop / expected_drop - 1.0) * 100, 100)
                
                # Estimate leak location (closer to sensor with lower pressure)
                leak_location = self._estimate_leak_location(
                    sensor_a, sensor_b, pressure_drop, expected_drop
                )
                
                leak_candidates.append({
                    "segment": f"{sensor_a.name} -> {sensor_b.name}",
                    "sensor_a_id": sensor_a.id,
                    "sensor_b_id": sensor_b.id,
                    "pressure_drop": round(pressure_drop, 2),
                    "expected_drop": round(expected_drop, 2),
                    "leak_probability": round(leak_probability, 1),
                    "estimated_location": leak_location,
                    "severity": self._classify_leak_severity(leak_probability)
                })
        
        return {
            "status": "success",
            "pipeline_id": pipeline_id,
            "analysis_period_hours": time_window_hours,
            "sensors_analyzed": len(sensors),
            "leak_candidates": leak_candidates,
            "total_leaks_detected": len(leak_candidates)
        }
    
    def find_sensors_near_location(
        self, 
        latitude: float, 
        longitude: float, 
        radius_meters: int = 1000
    ) -> List[Dict]:
        """Find all sensors within radius of a location."""
        from geoalchemy2 import WKTElement
        
        point = WKTElement(f'POINT({longitude} {latitude})', srid=4326)
        
        sensors = self.db.query(Sensor).filter(
            ST_DWithin(
                Sensor.location,
                point,
                radius_meters
            )
        ).all()
        
        results = []
        for sensor in sensors:
            distance = self.db.query(
                ST_Distance(Sensor.location, point)
            ).filter(Sensor.id == sensor.id).scalar()
            
            results.append({
                "sensor_id": sensor.id,
                "name": sensor.name,
                "distance_meters": round(float(distance), 2),
                "latitude": sensor.latitude,
                "longitude": sensor.longitude
            })
        
        return sorted(results, key=lambda x: x['distance_meters'])
    
    def analyze_pipeline_health(self, pipeline_id: str) -> Dict:
        """Comprehensive pipeline health analysis."""
        pipeline = self.db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
        if not pipeline:
            return {"status": "error", "message": "Pipeline not found"}
        
        # Get all sensors on pipeline
        sensors = self.db.query(Sensor).filter(
            Sensor.pipeline_id == pipeline_id
        ).all()
        
        # Calculate metrics
        active_sensors = sum(1 for s in sensors if s.is_active)
        inactive_sensors = len(sensors) - active_sensors
        
        # Get recent alerts
        recent_alerts = self.db.query(Alert).filter(
            Alert.pipeline_id == pipeline_id,
            Alert.created_at >= datetime.utcnow() - timedelta(days=7),
            Alert.status == 'active'
        ).count()
        
        # Calculate average sensor health
        sensor_health_scores = []
        for sensor in sensors:
            if sensor.last_reading_at:
                time_since = (datetime.utcnow() - sensor.last_reading_at).total_seconds()
                if time_since < 300:  # 5 minutes
                    sensor_health_scores.append(1.0)
                elif time_since < 3600:  # 1 hour
                    sensor_health_scores.append(0.7)
                elif time_since < 86400:  # 1 day
                    sensor_health_scores.append(0.4)
                else:
                    sensor_health_scores.append(0.1)
        
        if HAS_NUMPY:
            avg_health = np.mean(sensor_health_scores) if sensor_health_scores else 0.0
        else:
            avg_health = sum(sensor_health_scores) / len(sensor_health_scores) if sensor_health_scores else 0.0
        
        # Overall health score
        health_score = (
            (active_sensors / len(sensors) if sensors else 0) * 0.4 +
            avg_health * 0.4 +
            (1.0 - min(recent_alerts / 10, 1.0)) * 0.2
        ) * 100
        
        return {
            "pipeline_id": pipeline_id,
            "pipeline_name": pipeline.name,
            "health_score": round(health_score, 1),
            "health_status": self._get_health_status(health_score),
            "total_sensors": len(sensors),
            "active_sensors": active_sensors,
            "inactive_sensors": inactive_sensors,
            "recent_alerts": recent_alerts,
            "length_km": pipeline.length_km,
            "material": pipeline.material,
            "installation_date": pipeline.installation_date.isoformat() if pipeline.installation_date else None
        }
    
    def create_pressure_heatmap(
        self, 
        municipality_id: str, 
        time_window_minutes: int = 60
    ) -> Dict:
        """Generate pressure heatmap data for visualization."""
        cutoff = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        # Get all pressure sensors with recent readings
        sensors = self.db.query(
            Sensor.id,
            Sensor.name,
            Sensor.latitude,
            Sensor.longitude,
            func.avg(SensorReading.value).label('avg_pressure')
        ).join(
            SensorReading, Sensor.id == SensorReading.sensor_id
        ).filter(
            Sensor.municipality_id == municipality_id,
            Sensor.sensor_type_id.like('%pressure%'),
            SensorReading.timestamp >= cutoff
        ).group_by(
            Sensor.id, Sensor.name, Sensor.latitude, Sensor.longitude
        ).all()
        
        heatmap_points = []
        for sensor in sensors:
            heatmap_points.append({
                "sensor_id": sensor.id,
                "name": sensor.name,
                "latitude": sensor.latitude,
                "longitude": sensor.longitude,
                "value": round(float(sensor.avg_pressure), 2),
                "intensity": self._normalize_pressure(sensor.avg_pressure)
            })
        
        return {
            "municipality_id": municipality_id,
            "time_window_minutes": time_window_minutes,
            "timestamp": datetime.utcnow().isoformat(),
            "points": heatmap_points,
            "total_points": len(heatmap_points)
        }
    
    def detect_burst_location(
        self, 
        alert_id: str
    ) -> Optional[Dict]:
        """Triangulate burst location using multiple sensor readings."""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert or not alert.sensor_id:
            return None
        
        # Get the sensor that triggered the alert
        primary_sensor = self.db.query(Sensor).filter(Sensor.id == alert.sensor_id).first()
        if not primary_sensor:
            return None
        
        # Find nearby sensors
        nearby_sensors = self.find_sensors_near_location(
            primary_sensor.latitude,
            primary_sensor.longitude,
            radius_meters=5000
        )
        
        # Analyze pressure patterns
        burst_indicators = []
        for sensor_info in nearby_sensors[:5]:  # Top 5 nearest
            sensor = self.db.query(Sensor).filter(Sensor.id == sensor_info['sensor_id']).first()
            
            # Get readings around alert time
            readings = self.db.query(SensorReading).filter(
                SensorReading.sensor_id == sensor.id,
                SensorReading.timestamp >= alert.created_at - timedelta(minutes=10),
                SensorReading.timestamp <= alert.created_at + timedelta(minutes=10)
            ).all()
            
            if readings:
                values = [r.value for r in readings]
                pressure_drop = max(values) - min(values)
                
                burst_indicators.append({
                    "sensor_id": sensor.id,
                    "distance_meters": sensor_info['distance_meters'],
                    "pressure_drop": round(pressure_drop, 2),
                    "latitude": sensor.latitude,
                    "longitude": sensor.longitude
                })
        
        # Estimate burst location (weighted by pressure drop and distance)
        if burst_indicators:
            total_weight = sum(
                ind['pressure_drop'] / (ind['distance_meters'] + 1)
                for ind in burst_indicators
            )
            
            if total_weight > 0:
                est_lat = sum(
                    ind['latitude'] * (ind['pressure_drop'] / (ind['distance_meters'] + 1))
                    for ind in burst_indicators
                ) / total_weight
                
                est_lon = sum(
                    ind['longitude'] * (ind['pressure_drop'] / (ind['distance_meters'] + 1))
                    for ind in burst_indicators
                ) / total_weight
                
                return {
                    "estimated_latitude": round(est_lat, 6),
                    "estimated_longitude": round(est_lon, 6),
                    "confidence": min(len(burst_indicators) / 5 * 100, 100),
                    "sensors_used": len(burst_indicators),
                    "indicators": burst_indicators
                }
        
        return None
    
    @staticmethod
    def _calculate_distance(sensor_a: Sensor, sensor_b: Sensor) -> float:
        """Calculate distance between two sensors in kilometers."""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth radius in km
        
        lat1, lon1 = radians(sensor_a.latitude), radians(sensor_a.longitude)
        lat2, lon2 = radians(sensor_b.latitude), radians(sensor_b.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    @staticmethod
    def _calculate_expected_pressure_drop(
        distance_km: float, 
        diameter_mm: float, 
        material: str
    ) -> float:
        """Calculate expected pressure drop based on pipeline characteristics."""
        # Simplified Darcy-Weisbach equation
        # Actual implementation would use more sophisticated hydraulic models
        
        friction_factors = {
            'steel': 0.015,
            'pvc': 0.009,
            'concrete': 0.012,
            'cast_iron': 0.014
        }
        
        friction = friction_factors.get(material.lower() if material else '', 0.012)
        
        # Pressure drop (bar) = friction * distance * flow_factor / diameter
        expected_drop = friction * distance_km * 10 / (diameter_mm / 1000)
        
        return max(expected_drop, 0.1)
    
    @staticmethod
    def _estimate_leak_location(
        sensor_a: Sensor, 
        sensor_b: Sensor, 
        actual_drop: float, 
        expected_drop: float
    ) -> Dict:
        """Estimate leak location between two sensors."""
        # Leak is likely closer to sensor with lower pressure
        # Simple linear interpolation
        
        excess_drop = actual_drop - expected_drop
        ratio = min(excess_drop / actual_drop, 1.0) if actual_drop > 0 else 0.5
        
        # Interpolate coordinates
        lat = sensor_a.latitude + (sensor_b.latitude - sensor_a.latitude) * ratio
        lon = sensor_a.longitude + (sensor_b.longitude - sensor_a.longitude) * ratio
        
        return {
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "confidence": round(ratio * 100, 1)
        }
    
    @staticmethod
    def _classify_leak_severity(probability: float) -> str:
        """Classify leak severity based on probability."""
        if probability >= 80:
            return "critical"
        elif probability >= 60:
            return "high"
        elif probability >= 40:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def _get_health_status(score: float) -> str:
        """Get health status from score."""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        elif score >= 40:
            return "poor"
        else:
            return "critical"
    
    @staticmethod
    def _normalize_pressure(pressure: float, min_p: float = 0.0, max_p: float = 10.0) -> float:
        """Normalize pressure value for heatmap intensity (0-1)."""
        return min(max((pressure - min_p) / (max_p - min_p), 0.0), 1.0)


def get_geospatial_service(db: Session) -> GeospatialAnalysisService:
    """Factory function to get geospatial service instance."""
    return GeospatialAnalysisService(db)
