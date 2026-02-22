"""Device authentication and registration service for IoT sensors."""
import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from sqlalchemy.orm import Session
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from ..core.config import settings
from ..core.security import get_password_hash, verify_password
from ..models.device_auth import DeviceAuthentication
from ..models.sensor import Sensor

logger = logging.getLogger(__name__)


class DeviceAuthService:
    """Service for device authentication, registration, and certificate management"""
    
    # API Key settings
    API_KEY_LENGTH = 32
    API_KEY_PREFIX = "sk_water_"
    
    # Certificate settings
    CERT_VALIDITY_DAYS = 365
    RSA_KEY_SIZE = 2048
    
    # Heartbeat settings
    HEARTBEAT_TIMEOUT_SECONDS = 300  # 5 minutes
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key for device"""
        random_part = secrets.token_urlsafe(DeviceAuthService.API_KEY_LENGTH)
        return f"{DeviceAuthService.API_KEY_PREFIX}{random_part}"
    
    @staticmethod
    def register_device(
        db: Session,
        sensor_id: str,
        device_id: str,
        authentication_method: str = "api_key",  # api_key, certificate, mqtt
        certificate_pem: Optional[str] = None,
        mqtt_password: Optional[str] = None,
    ) -> Tuple[bool, str, Dict]:
        """
        Register a device with authentication credentials
        
        Args:
            db: Database session
            sensor_id: Associated sensor ID
            device_id: Device identifier
            authentication_method: Type of authentication to use
            certificate_pem: Optional PEM-encoded certificate
            mqtt_password: Optional MQTT password
        
        Returns:
            Tuple of (success, message, credentials)
        """
        try:
            # Check if sensor exists
            sensor = db.query(Sensor).filter(Sensor.id == sensor_id).first()
            if not sensor:
                return False, "Sensor not found", {}
            
            # Check if device already registered
            existing = db.query(DeviceAuthentication).filter(
                DeviceAuthentication.sensor_id == sensor_id
            ).first()
            
            if existing:
                return False, "Device already registered for this sensor", {}
            
            # Generate credentials based on method
            credentials = {}
            
            if authentication_method == "api_key":
                api_key = DeviceAuthService.generate_api_key()
                credentials["api_key"] = api_key
                
                device_auth = DeviceAuthentication(
                    sensor_id=sensor_id,
                    device_id=device_id,
                    api_key=api_key,
                    is_active=True,
                    expires_at=datetime.utcnow() + timedelta(days=365)
                )
            
            elif authentication_method == "certificate":
                if not certificate_pem:
                    return False, "Certificate required for certificate auth", {}
                
                cert_fingerprint = DeviceAuthService._get_cert_fingerprint(certificate_pem)
                credentials["certificate_fingerprint"] = cert_fingerprint
                
                device_auth = DeviceAuthentication(
                    sensor_id=sensor_id,
                    device_id=device_id,
                    certificate_pem=certificate_pem,
                    certificate_fingerprint=cert_fingerprint,
                    is_active=True,
                    expires_at=datetime.utcnow() + timedelta(days=365)
                )
            
            elif authentication_method == "mqtt":
                mqtt_user = f"sensor_{device_id}"
                mqtt_pass = secrets.token_urlsafe(24)
                mqtt_pass_hash = get_password_hash(mqtt_pass)
                credentials["mqtt_username"] = mqtt_user
                credentials["mqtt_password"] = mqtt_pass
                
                device_auth = DeviceAuthentication(
                    sensor_id=sensor_id,
                    device_id=device_id,
                    mqtt_username=mqtt_user,
                    mqtt_password_hash=mqtt_pass_hash,
                    is_active=True,
                    expires_at=datetime.utcnow() + timedelta(days=365)
                )
            
            else:
                return False, f"Unknown authentication method: {authentication_method}", {}
            
            db.add(device_auth)
            db.commit()
            
            logger.info(f"Device registered: {device_id} with {authentication_method}")
            return True, "Device registered successfully", credentials
        
        except Exception as e:
            db.rollback()
            logger.error(f"Device registration failed: {e}")
            return False, f"Registration failed: {str(e)}", {}
    
    @staticmethod
    def authenticate_device(
        db: Session,
        device_id: str,
        authentication_type: str,
        credential: str,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Authenticate a device with its credentials
        
        Args:
            db: Database session
            device_id: Device identifier
            authentication_type: Type of authentication (api_key, certificate_fingerprint, mqtt_password)
            credential: The credential to verify
        
        Returns:
            Tuple of (success, message, sensor_id)
        """
        try:
            device_auth = db.query(DeviceAuthentication).filter(
                DeviceAuthentication.device_id == device_id
            ).first()
            
            if not device_auth:
                logger.warning(f"Device authentication failed: device not found {device_id}")
                return False, "Device not registered", None
            
            if not device_auth.is_active:
                logger.warning(f"Device authentication failed: inactive device {device_id}")
                return False, "Device is inactive", None
            
            # Check expiration
            if device_auth.expires_at and datetime.utcnow() > device_auth.expires_at:
                logger.warning(f"Device authentication failed: expired credentials {device_id}")
                return False, "Device credentials expired", None
            
            # Verify credential based on type
            authenticated = False
            
            if authentication_type == "api_key":
                authenticated = secrets.compare_digest(device_auth.api_key, credential)
            
            elif authentication_type == "certificate_fingerprint":
                authenticated = secrets.compare_digest(
                    device_auth.certificate_fingerprint,
                    credential
                )
            
            elif authentication_type == "mqtt_password":
                authenticated = verify_password(credential, device_auth.mqtt_password_hash)
            
            else:
                return False, f"Unknown authentication type: {authentication_type}", None
            
            if authenticated:
                # Update last authenticated timestamp
                device_auth.last_authenticated = datetime.utcnow()
                db.commit()
                
                logger.info(f"Device authenticated successfully: {device_id}")
                return True, "Authentication successful", device_auth.sensor_id
            
            else:
                logger.warning(f"Device authentication failed: invalid credentials {device_id}")
                return False, "Invalid credentials", None
        
        except Exception as e:
            logger.error(f"Device authentication error: {e}")
            return False, f"Authentication error: {str(e)}", None
    
    @staticmethod
    def generate_certificate(
        device_id: str,
        common_name: str,
        validity_days: int = CERT_VALIDITY_DAYS
    ) -> Tuple[bool, str, Dict]:
        """
        Generate a self-signed certificate for a device
        
        Args:
            device_id: Device identifier
            common_name: Common name for certificate
            validity_days: Certificate validity period
        
        Returns:
            Tuple of (success, message, certificate_data)
        """
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=DeviceAuthService.RSA_KEY_SIZE,
                backend=default_backend()
            )
            
            # Build certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"State"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Water Authority"),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
                x509.NameAttribute(NameOID.SERIAL_NUMBER, device_id),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=validity_days)
            ).sign(private_key, hashes.SHA256(), default_backend())
            
            # Serialize certificate and key
            cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
            key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            
            cert_fingerprint = DeviceAuthService._get_cert_fingerprint(cert_pem)
            
            return True, "Certificate generated", {
                "certificate_pem": cert_pem,
                "private_key_pem": key_pem,
                "certificate_fingerprint": cert_fingerprint,
                "validity_days": validity_days,
            }
        
        except Exception as e:
            logger.error(f"Certificate generation failed: {e}")
            return False, f"Certificate generation failed: {str(e)}", {}
    
    @staticmethod
    def _get_cert_fingerprint(cert_pem: str) -> str:
        """Calculate SHA-256 fingerprint of certificate"""
        try:
            cert = x509.load_pem_x509_certificate(
                cert_pem.encode('utf-8'),
                default_backend()
            )
            fingerprint = cert.fingerprint(hashes.SHA256()).hex()
            return fingerprint
        except Exception as e:
            logger.error(f"Failed to calculate certificate fingerprint: {e}")
            return ""
    
    @staticmethod
    def refresh_api_key(db: Session, device_id: str) -> Tuple[bool, str, Optional[str]]:
        """Refresh API key for a device"""
        try:
            device_auth = db.query(DeviceAuthentication).filter(
                DeviceAuthentication.device_id == device_id
            ).first()
            
            if not device_auth:
                return False, "Device not found", None
            
            new_api_key = DeviceAuthService.generate_api_key()
            device_auth.api_key = new_api_key
            device_auth.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"API key refreshed for device: {device_id}")
            return True, "API key refreshed", new_api_key
        
        except Exception as e:
            db.rollback()
            logger.error(f"API key refresh failed: {e}")
            return False, f"Refresh failed: {str(e)}", None
    
    @staticmethod
    def deactivate_device(db: Session, device_id: str) -> Tuple[bool, str]:
        """Deactivate a device"""
        try:
            device_auth = db.query(DeviceAuthentication).filter(
                DeviceAuthentication.device_id == device_id
            ).first()
            
            if not device_auth:
                return False, "Device not found"
            
            device_auth.is_active = False
            device_auth.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Device deactivated: {device_id}")
            return True, "Device deactivated"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Device deactivation failed: {e}")
            return False, f"Deactivation failed: {str(e)}"
    
    @staticmethod
    def reactivate_device(db: Session, device_id: str) -> Tuple[bool, str]:
        """Reactivate a device"""
        try:
            device_auth = db.query(DeviceAuthentication).filter(
                DeviceAuthentication.device_id == device_id
            ).first()
            
            if not device_auth:
                return False, "Device not found"
            
            device_auth.is_active = True
            device_auth.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Device reactivated: {device_id}")
            return True, "Device reactivated"
        
        except Exception as e:
            db.rollback()
            logger.error(f"Device reactivation failed: {e}")
            return False, f"Reactivation failed: {str(e)}"
    
    @staticmethod
    def get_device_info(db: Session, device_id: str) -> Optional[Dict]:
        """Get device information"""
        try:
            device_auth = db.query(DeviceAuthentication).filter(
                DeviceAuthentication.device_id == device_id
            ).first()
            
            if not device_auth:
                return None
            
            return {
                "device_id": device_auth.device_id,
                "sensor_id": device_auth.sensor_id,
                "is_active": device_auth.is_active,
                "last_authenticated": device_auth.last_authenticated.isoformat() if device_auth.last_authenticated else None,
                "expires_at": device_auth.expires_at.isoformat() if device_auth.expires_at else None,
                "created_at": device_auth.created_at.isoformat(),
                "updated_at": device_auth.updated_at.isoformat(),
                "has_api_key": bool(device_auth.api_key),
                "has_certificate": bool(device_auth.certificate_pem),
                "has_mqtt_auth": bool(device_auth.mqtt_username),
            }
        
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return None
    
    @staticmethod
    def check_device_heartbeat(
        db: Session,
        device_id: str,
        timeout_seconds: int = HEARTBEAT_TIMEOUT_SECONDS
    ) -> bool:
        """Check if device has recent heartbeat"""
        try:
            device_auth = db.query(DeviceAuthentication).filter(
                DeviceAuthentication.device_id == device_id
            ).first()
            
            if not device_auth or not device_auth.last_authenticated:
                return False
            
            elapsed = (datetime.utcnow() - device_auth.last_authenticated).total_seconds()
            return elapsed <= timeout_seconds
        
        except Exception as e:
            logger.error(f"Heartbeat check failed: {e}")
            return False


# Global device auth service instance
device_auth_service = DeviceAuthService()
