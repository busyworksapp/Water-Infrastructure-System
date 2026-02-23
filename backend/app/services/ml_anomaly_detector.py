"""Advanced machine learning anomaly detection for water infrastructure monitoring."""
try:
    import numpy as np
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    HAS_ML = True
except ImportError:
    HAS_ML = False
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

from ..core.database import SessionLocal
from ..models.sensor import Sensor, SensorReading
from ..models.alert import Alert

logger = logging.getLogger(__name__)


class MLAnomalyDetector:
    """Machine learning-based anomaly detection for sensor data."""
    
    def __init__(self, contamination: float = 0.1):
        """
        Initialize ML anomaly detector.
        
        Args:
            contamination: Expected proportion of outliers in the dataset
        """
        self.contamination = contamination
        self.models: Dict[str, IsolationForest] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.trained_sensors: set = set()
    
    def train_sensor_model(
        self, 
        sensor_id: str, 
        training_days: int = 30,
        min_samples: int = 100
    ) -> bool:
        """
        Train anomaly detection model for a specific sensor.
        
        Args:
            sensor_id: Sensor identifier
            training_days: Number of days of historical data to use
            min_samples: Minimum number of samples required for training
            
        Returns:
            True if training successful, False otherwise
        """
        try:
            db = SessionLocal()
            cutoff = datetime.utcnow() - timedelta(days=training_days)
            
            readings = db.query(SensorReading).filter(
                SensorReading.sensor_id == sensor_id,
                SensorReading.timestamp >= cutoff,
                SensorReading.is_anomaly == False  # Train only on normal data
            ).all()
            
            db.close()
            
            if len(readings) < min_samples:
                logger.warning(
                    f"Insufficient data for sensor {sensor_id}: "
                    f"{len(readings)} samples (minimum {min_samples})"
                )
                return False
            
            # Extract features
            features = self._extract_features(readings)
            
            # Scale features
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(features)
            
            # Train Isolation Forest
            model = IsolationForest(
                contamination=self.contamination,
                random_state=42,
                n_estimators=100
            )
            model.fit(scaled_features)
            
            # Store model and scaler
            self.models[sensor_id] = model
            self.scalers[sensor_id] = scaler
            self.trained_sensors.add(sensor_id)
            
            logger.info(
                f"Trained anomaly detection model for sensor {sensor_id} "
                f"with {len(readings)} samples"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to train model for sensor {sensor_id}: {e}")
            return False
    
    def detect_anomaly(
        self, 
        sensor_id: str, 
        reading: SensorReading,
        context_readings: Optional[List[SensorReading]] = None
    ) -> Tuple[bool, float, Dict]:
        """
        Detect if a reading is anomalous using ML model.
        
        Args:
            sensor_id: Sensor identifier
            reading: Current sensor reading
            context_readings: Recent readings for context (optional)
            
        Returns:
            Tuple of (is_anomaly, confidence_score, details)
        """
        try:
            # Check if model is trained
            if sensor_id not in self.trained_sensors:
                logger.debug(f"No trained model for sensor {sensor_id}")
                return False, 0.0, {"reason": "model_not_trained"}
            
            model = self.models[sensor_id]
            scaler = self.scalers[sensor_id]
            
            # Extract features for current reading
            if context_readings:
                all_readings = context_readings + [reading]
            else:
                all_readings = [reading]
            
            features = self._extract_features(all_readings)
            current_features = features[-1:] # Last row
            
            # Scale features
            scaled_features = scaler.transform(current_features)
            
            # Predict anomaly
            prediction = model.predict(scaled_features)[0]
            anomaly_score = model.score_samples(scaled_features)[0]
            
            is_anomaly = prediction == -1
            confidence = abs(anomaly_score)
            
            details = {
                "method": "isolation_forest",
                "anomaly_score": float(anomaly_score),
                "confidence": float(confidence),
                "threshold": self.contamination
            }
            
            return is_anomaly, confidence, details
            
        except Exception as e:
            logger.error(f"Anomaly detection failed for sensor {sensor_id}: {e}")
            return False, 0.0, {"error": str(e)}
    
    def _extract_features(self, readings: List[SensorReading]) -> np.ndarray:
        """
        Extract features from sensor readings for ML model.
        
        Features include:
        - Raw value
        - Rate of change
        - Rolling statistics
        - Time-based features
        """
        features = []
        
        for i, reading in enumerate(readings):
            feature_vector = [reading.value]
            
            # Rate of change
            if i > 0:
                time_diff = (reading.timestamp - readings[i-1].timestamp).total_seconds()
                if time_diff > 0:
                    rate_of_change = (reading.value - readings[i-1].value) / time_diff
                else:
                    rate_of_change = 0.0
            else:
                rate_of_change = 0.0
            feature_vector.append(rate_of_change)
            
            # Rolling statistics (last 5 readings)
            window_start = max(0, i - 4)
            window_values = [r.value for r in readings[window_start:i+1]]
            
            if len(window_values) > 1:
                feature_vector.extend([
                    np.mean(window_values),
                    np.std(window_values),
                    np.min(window_values),
                    np.max(window_values)
                ])
            else:
                feature_vector.extend([reading.value, 0.0, reading.value, reading.value])
            
            # Time-based features
            hour = reading.timestamp.hour
            day_of_week = reading.timestamp.weekday()
            feature_vector.extend([
                np.sin(2 * np.pi * hour / 24),  # Cyclical hour encoding
                np.cos(2 * np.pi * hour / 24),
                day_of_week
            ])
            
            features.append(feature_vector)
        
        return np.array(features)
    
    def retrain_all_models(self, training_days: int = 30):
        """Retrain all sensor models with latest data."""
        db = SessionLocal()
        sensors = db.query(Sensor).filter(Sensor.is_active == True).all()
        db.close()
        
        success_count = 0
        for sensor in sensors:
            if self.train_sensor_model(sensor.id, training_days):
                success_count += 1
        
        logger.info(
            f"Retrained {success_count}/{len(sensors)} sensor models"
        )
        return success_count


class HybridAnomalyDetector:
    """Hybrid anomaly detector combining statistical and ML methods."""
    
    def __init__(self):
        self.ml_detector = MLAnomalyDetector()
        self.statistical_thresholds = {}
    
    def detect(
        self, 
        sensor_id: str, 
        reading: SensorReading,
        sensor: Sensor
    ) -> Tuple[bool, str, float, Dict]:
        """
        Detect anomalies using hybrid approach.
        
        Returns:
            Tuple of (is_anomaly, detection_method, confidence, details)
        """
        # Method 1: Statistical threshold check
        stat_anomaly, stat_details = self._statistical_check(reading, sensor)
        
        # Method 2: Rate of change check
        rate_anomaly, rate_details = self._rate_of_change_check(sensor_id, reading)
        
        # Method 3: ML-based detection
        ml_anomaly, ml_confidence, ml_details = self.ml_detector.detect_anomaly(
            sensor_id, reading
        )
        
        # Combine results
        if stat_anomaly:
            return True, "statistical", 0.9, stat_details
        elif rate_anomaly:
            return True, "rate_of_change", 0.8, rate_details
        elif ml_anomaly:
            return True, "machine_learning", ml_confidence, ml_details
        else:
            return False, "none", 0.0, {}
    
    def _statistical_check(
        self, 
        reading: SensorReading, 
        sensor: Sensor
    ) -> Tuple[bool, Dict]:
        """Check if reading exceeds statistical thresholds."""
        if not sensor.baseline_mean or not sensor.baseline_std:
            return False, {}
        
        z_score = abs(reading.value - sensor.baseline_mean) / sensor.baseline_std
        
        if z_score > 3.0:  # 3 sigma rule
            return True, {
                "method": "z_score",
                "z_score": float(z_score),
                "threshold": 3.0,
                "baseline_mean": sensor.baseline_mean,
                "baseline_std": sensor.baseline_std
            }
        
        return False, {}
    
    def _rate_of_change_check(
        self, 
        sensor_id: str, 
        reading: SensorReading
    ) -> Tuple[bool, Dict]:
        """Check for sudden rate of change."""
        try:
            db = SessionLocal()
            
            # Get last reading
            last_reading = db.query(SensorReading).filter(
                SensorReading.sensor_id == sensor_id,
                SensorReading.timestamp < reading.timestamp
            ).order_by(SensorReading.timestamp.desc()).first()
            
            db.close()
            
            if not last_reading:
                return False, {}
            
            time_diff = (reading.timestamp - last_reading.timestamp).total_seconds()
            if time_diff == 0:
                return False, {}
            
            rate = abs(reading.value - last_reading.value) / time_diff
            
            # Threshold depends on sensor type (configurable)
            threshold = 1.0  # Default threshold
            
            if rate > threshold:
                return True, {
                    "method": "rate_of_change",
                    "rate": float(rate),
                    "threshold": threshold,
                    "time_diff": time_diff
                }
            
            return False, {}
            
        except Exception as e:
            logger.error(f"Rate of change check failed: {e}")
            return False, {}


# Global detector instance
hybrid_detector = HybridAnomalyDetector()
