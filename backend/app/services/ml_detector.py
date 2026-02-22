from typing import Tuple, Optional, List
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MLAnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42, n_estimators=200)
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_path = "models/anomaly_detector.pkl"
        self.metrics = {"accuracy": 0.0, "last_trained": None, "samples": 0}
    
    def train(self, historical_data: np.ndarray, labels: Optional[np.ndarray] = None) -> bool:
        """Train the model on historical data with optional labels"""
        try:
            if len(historical_data) < 100:
                logger.warning("Insufficient data for training")
                return False
            
            # Reshape and normalize
            data_reshaped = historical_data.reshape(-1, 1)
            scaled_data = self.scaler.fit_transform(data_reshaped)
            
            # Train model
            self.model.fit(scaled_data)
            self.is_trained = True
            
            # Update metrics
            self.metrics["samples"] = len(historical_data)
            self.metrics["last_trained"] = datetime.utcnow().isoformat()
            
            # Calculate training accuracy if labels provided
            if labels is not None:
                predictions = self.model.predict(scaled_data)
                accuracy = np.mean(predictions == labels)
                self.metrics["accuracy"] = float(accuracy)
            
            # Save model
            self._save_model()
            
            logger.info(f"Model trained on {len(historical_data)} samples, accuracy: {self.metrics['accuracy']:.2%}")
            return True
            
        except Exception as e:
            logger.error(f"Training error: {e}")
            return False
    
    def predict(self, value: float, context: Optional[List[float]] = None) -> Tuple[bool, float]:
        """Predict if value is anomalous with optional context"""
        try:
            if not self.is_trained:
                self._load_model()
            
            if not self.is_trained:
                return False, 0.0
            
            # Scale value
            scaled_value = self.scaler.transform([[value]])
            
            # Predict
            prediction = self.model.predict(scaled_value)[0]
            score = self.model.score_samples(scaled_value)[0]
            
            # -1 means anomaly, 1 means normal
            is_anomaly = prediction == -1
            
            # Normalize score to 0-1 range
            anomaly_score = 1.0 / (1.0 + np.exp(score)) if is_anomaly else 0.0
            
            return is_anomaly, min(anomaly_score, 1.0)
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return False, 0.0
    
    def predict_batch(self, values: List[float]) -> List[Tuple[bool, float]]:
        """Predict anomalies for multiple values efficiently"""
        try:
            if not self.is_trained:
                self._load_model()
            
            if not self.is_trained:
                return [(False, 0.0)] * len(values)
            
            # Scale values
            values_array = np.array(values).reshape(-1, 1)
            scaled_values = self.scaler.transform(values_array)
            
            # Predict
            predictions = self.model.predict(scaled_values)
            scores = self.model.score_samples(scaled_values)
            
            results = []
            for pred, score in zip(predictions, scores):
                is_anomaly = pred == -1
                anomaly_score = 1.0 / (1.0 + np.exp(score)) if is_anomaly else 0.0
                results.append((is_anomaly, min(anomaly_score, 1.0)))
            
            return results
            
        except Exception as e:
            logger.error(f"Batch prediction error: {e}")
            return [(False, 0.0)] * len(values)
    
    def get_metrics(self) -> dict:
        """Get model performance metrics"""
        return self.metrics.copy()
    
    def _save_model(self):
        """Save trained model to disk"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump({
                    'model': self.model,
                    'scaler': self.scaler,
                    'metrics': self.metrics
                }, f)
            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def _load_model(self):
        """Load trained model from disk"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.scaler = data['scaler']
                    self.metrics = data.get('metrics', self.metrics)
                    self.is_trained = True
                logger.info(f"Model loaded: {self.metrics['samples']} samples, trained {self.metrics['last_trained']}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
