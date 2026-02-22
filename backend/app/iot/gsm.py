"""GSM/GPRS gateway integration for cellular-based sensors."""
import logging
from typing import Dict, Optional
from datetime import datetime

from ..core.database import SessionLocal
from ..services.ingestion_service import ingestion_service

logger = logging.getLogger(__name__)


class GSMGateway:
    """Handle GSM/GPRS sensor communications."""
    
    async def process_sms_message(
        self, 
        phone_number: str, 
        message: str,
        timestamp: Optional[datetime] = None
    ) -> Dict:
        """
        Process sensor data received via SMS.
        
        SMS format: SENSOR_ID:VALUE:UNIT
        Example: "WS001:3.5:bar"
        """
        db = SessionLocal()
        try:
            # Parse SMS message
            parts = message.strip().split(":")
            if len(parts) < 2:
                raise ValueError("Invalid SMS format. Expected: SENSOR_ID:VALUE[:UNIT]")
            
            sensor_id = parts[0]
            value = float(parts[1])
            unit = parts[2] if len(parts) > 2 else None
            
            payload = {
                "value": value,
                "unit": unit,
                "timestamp": timestamp or datetime.utcnow(),
                "quality_score": 0.8,  # SMS has moderate reliability
                "phone_number": phone_number,
                "raw_message": message
            }
            
            result = ingestion_service.process_reading(
                db,
                device_id=sensor_id,
                protocol="gsm_sms",
                payload=payload,
                enforce_api_key=False
            )
            
            logger.info(f"GSM SMS processed from {phone_number} for sensor {sensor_id}")
            return {"status": "success", **result}
            
        except Exception as e:
            db.rollback()
            logger.error(f"GSM SMS processing failed: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            db.close()
    
    async def process_gprs_message(
        self, 
        imei: str, 
        data: Dict
    ) -> Dict:
        """
        Process sensor data received via GPRS/HTTP.
        
        Expected data format:
        {
            "sensor_id": "WS001",
            "value": 3.5,
            "unit": "bar",
            "timestamp": "2024-01-15T10:30:00Z",
            "signal_strength": 85,
            "battery_level": 75
        }
        """
        db = SessionLocal()
        try:
            if "value" not in data:
                raise ValueError("Missing value in GPRS payload")
            
            payload = {
                "value": data["value"],
                "unit": data.get("unit"),
                "timestamp": data.get("timestamp"),
                "quality_score": self._calculate_quality(data),
                "signal_strength": data.get("signal_strength"),
                "battery_level": data.get("battery_level"),
                "imei": imei,
                "raw_data": data
            }
            
            sensor_id = data.get("sensor_id", imei)
            
            result = ingestion_service.process_reading(
                db,
                device_id=sensor_id,
                protocol="gsm_gprs",
                payload=payload,
                api_key=data.get("api_key"),
                enforce_api_key=False
            )
            
            logger.info(f"GSM GPRS processed from IMEI {imei} for sensor {sensor_id}")
            return {"status": "success", **result}
            
        except Exception as e:
            db.rollback()
            logger.error(f"GSM GPRS processing failed for IMEI {imei}: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            db.close()
    
    async def process_ussd_message(
        self, 
        phone_number: str, 
        ussd_code: str,
        response: str
    ) -> Dict:
        """
        Process sensor data received via USSD.
        
        USSD format: *123*SENSOR_ID*VALUE#
        Response: Sensor reading value
        """
        db = SessionLocal()
        try:
            # Parse USSD response
            # Expected format: "VALUE UNIT" or just "VALUE"
            parts = response.strip().split()
            value = float(parts[0])
            unit = parts[1] if len(parts) > 1 else None
            
            # Extract sensor ID from USSD code
            code_parts = ussd_code.strip("*#").split("*")
            sensor_id = code_parts[1] if len(code_parts) > 1 else phone_number
            
            payload = {
                "value": value,
                "unit": unit,
                "timestamp": datetime.utcnow(),
                "quality_score": 0.7,  # USSD has lower reliability
                "phone_number": phone_number,
                "ussd_code": ussd_code,
                "raw_response": response
            }
            
            result = ingestion_service.process_reading(
                db,
                device_id=sensor_id,
                protocol="gsm_ussd",
                payload=payload,
                enforce_api_key=False
            )
            
            logger.info(f"GSM USSD processed from {phone_number} for sensor {sensor_id}")
            return {"status": "success", **result}
            
        except Exception as e:
            db.rollback()
            logger.error(f"GSM USSD processing failed: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            db.close()
    
    @staticmethod
    def _calculate_quality(data: Dict) -> float:
        """Calculate quality score based on signal and battery."""
        signal = float(data.get("signal_strength", 50))
        battery = float(data.get("battery_level", 100))
        
        # Normalize to 0-1 range
        signal_score = max(0.0, min(1.0, signal / 100))
        battery_score = max(0.0, min(1.0, battery / 100))
        
        # Weighted average (signal more important)
        quality = (signal_score * 0.7) + (battery_score * 0.3)
        
        return round(quality, 4)
    
    def generate_sms_response(self, status: str, message: str = "") -> str:
        """Generate SMS response to send back to sensor."""
        if status == "success":
            return "OK: Data received"
        else:
            return f"ERROR: {message}"


# Global GSM gateway instance
gsm_gateway = GSMGateway()
