from typing import Generator
import logging

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import QueuePool

from .config import settings

logger = logging.getLogger(__name__)

# Determine database URL and engine configuration
DATABASE_URL = settings.active_database_url
IS_POSTGRES = settings.DATABASE_MODE.lower() == "postgres"
IS_MYSQL = settings.DATABASE_MODE.lower() == "mysql"

# Log database connection info (mask password)
masked_url = DATABASE_URL.replace("://", "://***:***@") if DATABASE_URL else "Not configured"
logger.info(f"Initializing {settings.DATABASE_MODE.upper()} database: {masked_url}")

# Engine configuration for different databases
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_size": settings.DB_POOL_SIZE,
    "max_overflow": settings.DB_MAX_OVERFLOW,
    "pool_timeout": 60,  # Increased timeout for remote Railway connections
    "echo": settings.DB_ECHO,
    "future": True,
    "poolclass": QueuePool,
    "connect_args": {
        "connect_timeout": 30,  # Longer timeout for initial connection
    }
}

# PostgreSQL-specific settings
if IS_POSTGRES:
    engine_kwargs["connect_args"].update({
        "connect_timeout": 30,
        "application_name": "water-monitoring",
    })

# MySQL-specific settings
if IS_MYSQL:
    engine_kwargs["connect_args"].update({
        "connect_timeout": 30,
        "read_timeout": 60,
        "write_timeout": 60,
        "charset": "utf8mb4",
    })
    engine_kwargs["pool_recycle"] = 3600  # Recycle connections every hour
    engine_kwargs["pool_pre_ping"] = True  # Test connections before using

engine = create_engine(DATABASE_URL, **engine_kwargs)

# PostGIS extension auto-load for PostgreSQL
if IS_POSTGRES and settings.auto_enable_postgis:
    @event.listens_for(engine, "connect")
    def load_spatialite(dbapi_conn, connection_record):
        """Auto-enable PostGIS on PostgreSQL connections"""
        try:
            with dbapi_conn.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
                cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology")
                dbapi_conn.commit()
            logger.info("PostGIS extension enabled")
        except Exception as e:
            logger.warning(f"Failed to enable PostGIS: {e}")

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)
Base = declarative_base()


def get_db() -> Generator:
    """Database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


async def check_database_connection() -> bool:
    """Check if database is accessible"""
    try:
        with engine.connect() as connection:
            if IS_POSTGRES:
                result = connection.execute("SELECT 1")
            else:
                result = connection.execute("SELECT 1 as health")
            return result.fetchone() is not None
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

