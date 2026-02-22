"""Cache warming service for performance optimization."""
from typing import Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import json
import logging

from ..core.cache import cache
from ..models.sensor import Sensor
from ..models.municipality import Municipality
from ..models.alert import Alert

logger = logging.getLogger(__name__)

class CacheWarmer:
    """Preload frequently accessed data into cache."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def warm_all(self) -> Dict:
        """Warm all critical caches."""
        results = {
            "municipalities": self.warm_municipalities(),
            "active_sensors": self.warm_active_sensors(),
            "critical_alerts": self.warm_critical_alerts(),
            "sensor_stats": self.warm_sensor_stats()
        }
        return results
    
    def warm_municipalities(self) -> bool:
        """Cache all municipalities."""
        try:
            municipalities = self.db.query(Municipality).filter(Municipality.is_active == True).all()
            for muni in municipalities:
                cache.set(f"municipality:{muni.id}", {
                    "id": muni.id,
                    "name": muni.name,
                    "code": muni.code,
                    "region": muni.region
                }, ttl=3600)
            logger.info(f"Cached {len(municipalities)} municipalities")
            return True
        except Exception as e:
            logger.error(f"Municipality cache warming failed: {e}")
            return False
    
    def warm_active_sensors(self) -> bool:
        """Cache active sensors list."""
        try:
            sensors = self.db.query(Sensor).filter(Sensor.is_active == True).all()
            sensor_data = [{"id": s.id, "name": s.name, "type": s.sensor_type} for s in sensors]
            cache.set("active_sensors", sensor_data, ttl=300)
            logger.info(f"Cached {len(sensors)} active sensors")
            return True
        except Exception as e:
            logger.error(f"Sensor cache warming failed: {e}")
            return False
    
    def warm_critical_alerts(self) -> bool:
        """Cache critical alerts."""
        try:
            alerts = self.db.query(Alert).filter(
                Alert.status == 'active',
                Alert.severity == 'critical'
            ).all()
            alert_data = [{"id": a.id, "type": a.alert_type, "sensor_id": a.sensor_id} for a in alerts]
            cache.set("critical_alerts", alert_data, ttl=60)
            logger.info(f"Cached {len(alerts)} critical alerts")
            return True
        except Exception as e:
            logger.error(f"Alert cache warming failed: {e}")
            return False
    
    def warm_sensor_stats(self) -> bool:
        """Cache sensor statistics."""
        try:
            total = self.db.query(func.count(Sensor.id)).scalar()
            active = self.db.query(func.count(Sensor.id)).filter(Sensor.is_active == True).scalar()
            cache.set("sensor_stats", {"total": total, "active": active}, ttl=300)
            return True
        except Exception as e:
            logger.error(f"Stats cache warming failed: {e}")
            return False
