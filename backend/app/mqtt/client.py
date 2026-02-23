import json
import logging
from typing import Any, Dict, Optional
import time
import threading

import paho.mqtt.client as mqtt

from ..core.config import settings
from ..core.database import SessionLocal
from ..services.ingestion_service import ingestion_service

logger = logging.getLogger(__name__)


class MQTTClient:
    """MQTT client with reconnection logic, TLS support, and proper error handling"""
    
    def __init__(self):
        self.client = mqtt.Client(
            client_id="water-monitoring-backend",
            clean_session=True,
            protocol=mqtt.MQTTv311
        )
        
        # Connection retry parameters
        self.reconnect_delay = 1  # Start with 1 second
        self.max_reconnect_delay = 60  # Max 60 seconds
        self.reconnect_count = 0
        self.is_connected = False
        self.reconnect_thread: Optional[threading.Thread] = None
        
        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe
        self.client.on_unsubscribe = self._on_unsubscribe
        
        # Set up authentication
        if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
            self.client.username_pw_set(
                settings.MQTT_USERNAME,
                settings.MQTT_PASSWORD
            )
            logger.info("MQTT authentication configured")
        
        # Set up TLS
        if settings.MQTT_TLS_ENABLED:
            try:
                self.client.tls_set(
                    ca_certs=settings.MQTT_TLS_CA_CERT,
                    certfile=settings.MQTT_TLS_CLIENT_CERT,
                    keyfile=settings.MQTT_TLS_CLIENT_KEY,
                    cert_reqs=mqtt.ssl.CERT_REQUIRED,
                    tls_version=mqtt.ssl.PROTOCOL_TLSv1_2,
                    ciphers=None
                )
                self.client.tls_insecure_set(False)
                logger.info("MQTT TLS enabled with certificates")
            except Exception as e:
                logger.error(f"MQTT TLS setup failed: {e}")
        
        # Set keep alive and other options
        self.client.reconnect_delay_set(min_delay=1, max_delay=60)

    def connect(self):
        """Connect to MQTT broker with error handling"""
        try:
            logger.info(
                f"Connecting to MQTT broker {settings.MQTT_BROKER_HOST}:"
                f"{settings.MQTT_BROKER_PORT}"
            )
            self.client.connect(
                settings.MQTT_BROKER_HOST,
                settings.MQTT_BROKER_PORT,
                keepalive=60
            )
            self.client.loop_start()
            logger.info("MQTT client started")
        except ConnectionRefusedError:
            logger.info("MQTT broker not available (optional service)")
        except Exception as e:
            logger.info(f"MQTT not configured: {e}")

    def disconnect(self):
        """Disconnect from MQTT broker"""
        try:
            self.is_connected = False
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT client disconnected")
        except Exception as e:
            logger.error(f"MQTT disconnect error: {e}")

    def _schedule_reconnect(self):
        """Schedule reconnection with exponential backoff"""
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            return
        
        self.reconnect_thread = threading.Thread(
            target=self._reconnect_with_backoff,
            daemon=True
        )
        self.reconnect_thread.start()

    def _reconnect_with_backoff(self):
        """Reconnect with exponential backoff"""
        self.reconnect_delay = min(
            self.reconnect_delay * 2,
            self.max_reconnect_delay
        )
        self.reconnect_count += 1
        
        # Only log first few attempts
        if self.reconnect_count <= 3:
            logger.info(f"MQTT reconnecting (attempt {self.reconnect_count})")
        
        time.sleep(self.reconnect_delay)
        
        try:
            self.client.reconnect()
            logger.info("MQTT reconnection successful")
        except Exception:
            # Silently fail after initial attempts
            if self.reconnect_count <= 3:
                logger.info("MQTT broker still unavailable")
            self._schedule_reconnect()

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Handle MQTT connection"""
        if rc == 0:
            self.is_connected = True
            self.reconnect_delay = 1  # Reset backoff on successful connection
            self.reconnect_count = 0
            logger.info("Connected to MQTT broker successfully")
            
            # Subscribe to sensor topics
            client.subscribe("sensors/+/data", qos=1)
            client.subscribe("sensors/+/status", qos=0)
            client.subscribe("sensors/+/heartbeat", qos=0)
            client.subscribe("system/+/command", qos=1)
            logger.info("Subscribed to sensor topics")
        else:
            self.is_connected = False
            error_messages = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized",
            }
            error_msg = error_messages.get(rc, f"Unknown error code {rc}")
            logger.error(f"MQTT connection failed: {error_msg}")
            
            # For authentication errors, don't retry
            if rc in [4, 5]:
                logger.error("MQTT authentication failed - check credentials")
            else:
                self._schedule_reconnect()

    @staticmethod
    def _on_disconnect(client, userdata, rc, properties=None):
        """Handle MQTT disconnection"""
        if rc == 0:
            logger.info("MQTT disconnected normally")
        else:
            logger.warning(f"Unexpected MQTT disconnection, code: {rc}")

    def _on_subscribe(self, client, userdata, mid, granted_qos, properties=None):
        """Handle subscription confirmation"""
        logger.debug(f"Subscription acknowledged with QoS: {granted_qos}")

    def _on_unsubscribe(self, client, userdata, mid, properties=None):
        """Handle unsubscription confirmation"""
        logger.debug("Unsubscription acknowledged")

    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic_parts = msg.topic.split("/")
            if len(topic_parts) < 3:
                logger.warning(f"Invalid topic format: {msg.topic}")
                return

            _, device_id, message_type = topic_parts[:3]
            
            try:
                payload = json.loads(msg.payload.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"Failed to decode MQTT payload for {device_id}: {e}")
                return

            if message_type == "data":
                self._handle_sensor_data(device_id, payload)
            elif message_type == "status":
                self._handle_status(device_id, payload)
            elif message_type == "heartbeat":
                self._handle_heartbeat(device_id, payload)
            elif message_type == "command":
                self._handle_command(device_id, payload)
            else:
                logger.debug(f"Unknown message type: {message_type}")
        
        except Exception as e:
            logger.error(f"MQTT message processing error: {e}", exc_info=True)

    def _handle_sensor_data(self, device_id: str, payload: Dict[str, Any]):
        """Process sensor data from MQTT"""
        db = SessionLocal()
        try:
            logger.debug(f"Processing MQTT data from {device_id}")
            ingestion_service.process_reading(
                db,
                device_id=device_id,
                protocol="mqtt",
                payload=payload,
                api_key=payload.get("api_key"),
                mqtt_password=payload.get("mqtt_password"),
                certificate_fingerprint=payload.get("certificate_fingerprint"),
                enforce_api_key=False,
            )
            logger.debug(f"MQTT data processed for {device_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"MQTT sensor data processing failed for {device_id}: {e}", exc_info=True)
        finally:
            db.close()

    def _handle_status(self, device_id: str, payload: Dict[str, Any]):
        """Handle sensor status updates from MQTT"""
        db = SessionLocal()
        try:
            from ..models.sensor import Sensor

            sensor = db.query(Sensor).filter(Sensor.device_id == device_id).first()
            if not sensor:
                logger.warning(f"Sensor not found: {device_id}")
                return
            
            # Update sensor status fields
            if payload.get("battery_level") is not None:
                sensor.battery_level = float(payload["battery_level"])
            if payload.get("signal_strength") is not None:
                sensor.signal_strength = float(payload["signal_strength"])
            if payload.get("firmware_version"):
                sensor.firmware_version = str(payload["firmware_version"])
            
            db.commit()
            logger.debug(f"Sensor status updated: {device_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"MQTT status update failed for {device_id}: {e}", exc_info=True)
        finally:
            db.close()

    def _handle_heartbeat(self, device_id: str, payload: Dict[str, Any]):
        """Handle sensor heartbeat from MQTT"""
        db = SessionLocal()
        try:
            from datetime import datetime
            from ..models.sensor import Sensor

            sensor = db.query(Sensor).filter(Sensor.device_id == device_id).first()
            if not sensor:
                logger.warning(f"Sensor not found for heartbeat: {device_id}")
                return
            
            sensor.last_reading_at = datetime.utcnow()
            db.commit()
            logger.debug(f"Heartbeat received from {device_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"MQTT heartbeat processing failed for {device_id}: {e}", exc_info=True)
        finally:
            db.close()

    def _handle_command(self, device_id: str, payload: Dict[str, Any]):
        """Handle system commands from MQTT"""
        try:
            command = payload.get("command")
            args = payload.get("args", {})
            
            logger.info(f"Processing MQTT command for {device_id}: {command}")
            
            if command == "restart":
                self.publish(f"sensors/{device_id}/response", {
                    "status": "acknowledged",
                    "command": "restart"
                })
            elif command == "update_config":
                self.publish(f"sensors/{device_id}/response", {
                    "status": "acknowledged",
                    "command": "update_config",
                    "config": args
                })
            else:
                logger.warning(f"Unknown command: {command}")
        
        except Exception as e:
            logger.error(f"MQTT command handling failed: {e}", exc_info=True)

    def publish(self, topic: str, payload: Dict[str, Any], qos: int = 1) -> bool:
        """Publish message to MQTT topic"""
        try:
            if not self.is_connected:
                logger.warning(f"MQTT not connected, cannot publish to {topic}")
                return False
            
            result = self.client.publish(
                topic,
                json.dumps(payload),
                qos=qos,
                retain=False
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"MQTT published to {topic}")
                return True
            else:
                logger.error(f"MQTT publish failed for {topic}: {result.rc}")
                return False
        
        except Exception as e:
            logger.error(f"MQTT publish error for {topic}: {e}", exc_info=True)
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get MQTT client status"""
        return {
            "connected": self.is_connected,
            "broker": f"{settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}",
            "reconnect_count": self.reconnect_count,
            "reconnect_delay": self.reconnect_delay,
        }


mqtt_client = MQTTClient()
