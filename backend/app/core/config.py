from typing import Optional, Union
import secrets
import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "National Water Infrastructure Monitoring System"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Database (MySQL or PostgreSQL) - supports Railway.app connection strings
    DATABASE_MODE: str = Field(default="mysql")  # "mysql" or "postgres"
    DATABASE_URL: Optional[str] = None  # Auto-parsed from environment or set explicitly
    DATABASE_URL_MYSQL: Optional[str] = None  # MySQL connection string (Railway compatible)
    DATABASE_URL_POSTGRES: Optional[str] = None  # PostgreSQL connection string (Railway compatible)
    ENABLE_POSTGIS_FEATURES: bool = Field(default=False)
    
    # Database optimization
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # S3-compatible object storage (AWS S3, Linode, Railway, etc.)
    S3_ENDPOINT: Optional[str] = None  # Custom endpoint for non-AWS S3 (e.g., https://t3.storageapi.dev)
    S3_REGION: str = "auto"  # AWS region or "auto" for S3-compatible services
    S3_BUCKET: Optional[str] = None  # Bucket name (e.g., "recorded-wrap-krk8vsj4wzi")
    S3_ACCESS_KEY: Optional[str] = None  # Access key ID
    S3_SECRET_KEY: Optional[str] = None  # Secret access key
    S3_STORAGE_CLASS: str = "STANDARD_IA"  # Default storage class for new uploads
    S3_BACKUP_PREFIX: str = "backups/"  # S3 prefix for backup files
    S3_ENABLED: bool = Field(default=False)  # Auto-set if bucket configured

    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(48))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "national-water-monitoring"
    JWT_AUDIENCE: str = "water-monitoring-clients"

    # MQTT
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    MQTT_TLS_ENABLED: bool = False
    MQTT_TLS_CA_CERT: Optional[str] = None
    MQTT_TLS_CLIENT_CERT: Optional[str] = None
    MQTT_TLS_CLIENT_KEY: Optional[str] = None

    # TCP ingestion
    TCP_HOST: str = "0.0.0.0"
    TCP_PORT: int = 9999

    # WebSocket
    WS_MESSAGE_QUEUE_SIZE: int = 1000
    WS_EVENT_REPLAY_LIMIT: int = 500

    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # Rate limiting / throttling
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_USER: int = 100
    RATE_LIMIT_PER_API_KEY: int = 1000

    # CORS / trusted origins (will be converted to list[str])
    CORS_ORIGINS: Union[str, list[str]] = Field(default="*")
    
    # Monitoring & Observability
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    METRICS_RETENTION_HOURS: int = 24
    
    # Backup & Recovery
    BACKUP_ENABLED: bool = True
    BACKUP_SCHEDULE: str = "0 2 * * *"  # Daily at 2 AM
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_COMPRESSION: bool = True
    
    # Security Hardening
    ENFORCE_HTTPS: bool = True
    SECURE_HEADERS_ENABLED: bool = True
    HSTS_MAX_AGE: int = 31536000  # 1 year
    CSP_ENABLED: bool = True
    ALLOW_ORIGINS_REGEX: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )
    
    def __init__(self, **data):
        super().__init__(**data)
        # Auto-initialize DATABASE_URL if not set
        if not self.DATABASE_URL:
            if self.DATABASE_MODE.lower() == "postgres" and self.DATABASE_URL_POSTGRES:
                self.DATABASE_URL = self.DATABASE_URL_POSTGRES
            elif self.DATABASE_MODE.lower() == "mysql" and self.DATABASE_URL_MYSQL:
                self.DATABASE_URL = self.DATABASE_URL_MYSQL
            else:
                # Use default based on mode
                if self.DATABASE_MODE.lower() == "postgres":
                    self.DATABASE_URL = "postgresql://user:password@localhost:5432/water_monitoring"
                else:
                    self.DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/water_monitoring"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        # Return as-is if already a list
        if isinstance(value, list):
            return value
        
        if isinstance(value, str):
            # Handle empty string
            if not value or value.strip() == "":
                return ["*"]
            
            cleaned = value.strip()
            
            # Handle single wildcard
            if cleaned == "*":
                return ["*"]
            
            # Handle JSON array format
            if cleaned.startswith("[") and cleaned.endswith("]"):
                try:
                    import json
                    return json.loads(cleaned)
                except:
                    # Fallback to manual parsing
                    cleaned = cleaned[1:-1]
            
            # Handle comma-separated values
            origins = [v.strip().strip('"').strip("'") for v in cleaned.split(",") if v.strip()]
            return origins if origins else ["*"]
        
        return ["*"]
    
    @field_validator("DATABASE_MODE", mode="before")
    @classmethod
    def validate_database_mode(cls, value):
        if value not in ["mysql", "postgres"]:
            raise ValueError(f"DATABASE_MODE must be 'mysql' or 'postgres', got {value}")
        return value.lower()
    
    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def validate_environment(cls, value):
        if value not in ["development", "staging", "production"]:
            raise ValueError("ENVIRONMENT must be one of development, staging, production")
        return value.lower()
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value):
        if not value or value == "change-me" or len(value) < 32:
            import warnings
            warnings.warn("SECRET_KEY should be at least 32 characters for production use")
        return value
    
    @field_validator("S3_BUCKET", mode="before")
    @classmethod
    def validate_s3_config(cls, value, info):
        """Validate S3 configuration consistency"""
        data = info.data
        if value:
            # If bucket is set, warn if credentials are missing
            if not (data.get("S3_ACCESS_KEY") and data.get("S3_SECRET_KEY")):
                import warnings
                warnings.warn("S3 bucket configured but credentials missing")
            # Auto-enable S3 if bucket is configured
            data["S3_ENABLED"] = True
        return value

    @property
    def resolved_celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def resolved_celery_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    @property
    def active_database_url(self) -> str:
        if self.DATABASE_MODE.lower() == "postgres" and self.DATABASE_URL_POSTGRES:
            return self.DATABASE_URL_POSTGRES
        return self.DATABASE_URL
    
    @property
    def auto_enable_postgis(self) -> bool:
        """Auto-enable PostGIS if using PostgreSQL"""
        if self.DATABASE_MODE.lower() == "postgres":
            return True
        return self.ENABLE_POSTGIS_FEATURES
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    def validate_production_settings(self) -> list[str]:
        """Validate critical settings for production deployment"""
        warnings = []
        if self.is_production:
            if self.DEBUG:
                warnings.append("DEBUG should be False in production")
            if self.CORS_ORIGINS == ["*"]:
                warnings.append("CORS_ORIGINS set to * in production")
            if not self.ENFORCE_HTTPS:
                warnings.append("ENFORCE_HTTPS should be True in production")
        return warnings


settings = Settings()
production_warnings = settings.validate_production_settings()
if production_warnings:
    import logging
    logger = logging.getLogger(__name__)
    for warning in production_warnings:
        logger.warning(f"Production configuration warning: {warning}")
