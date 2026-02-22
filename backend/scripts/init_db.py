"""Database bootstrap script for first-run provisioning."""
import os
import sys
from datetime import datetime

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

from app.core.database import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models import Municipality, Permission, Role, SystemSetting, User
from app.models.sensor import SensorType
from app.models.system import ProtocolConfiguration, ProtocolType


def init_database():
    print("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    print("Tables verified.")

    db = SessionLocal()
    try:
        permissions = [
            Permission(name="View Sensors", code="sensors.view", resource="sensors", action="view"),
            Permission(name="Manage Sensors", code="sensors.manage", resource="sensors", action="manage"),
            Permission(name="View Alerts", code="alerts.view", resource="alerts", action="view"),
            Permission(name="Manage Alerts", code="alerts.manage", resource="alerts", action="manage"),
            Permission(name="View Pipelines", code="pipelines.view", resource="pipelines", action="view"),
            Permission(name="Manage Pipelines", code="pipelines.manage", resource="pipelines", action="manage"),
            Permission(name="Manage Rules", code="rules.manage", resource="rules", action="manage"),
            Permission(name="System Admin", code="system.admin", resource="system", action="admin"),
        ]
        for permission in permissions:
            if not db.query(Permission).filter(Permission.code == permission.code).first():
                db.add(permission)
        db.commit()
        print("Permissions ensured.")

        default_roles = [
            Role(name="Super Administrator", code="super_admin", description="Full system access", is_system=True),
            Role(
                name="Municipality Administrator",
                code="municipality_admin",
                description="Municipality-level administration",
                is_system=True,
            ),
            Role(name="Operator", code="operator", description="Monitor and respond to alerts", is_system=True),
        ]
        for role in default_roles:
            if not db.query(Role).filter(Role.code == role.code).first():
                db.add(role)
        db.commit()

        super_admin_role = db.query(Role).filter(Role.code == "super_admin").first()
        if super_admin_role:
            super_admin_role.permissions = db.query(Permission).all()
            db.commit()
        print("Roles ensured.")

        municipality_code = os.getenv("BOOTSTRAP_MUNICIPALITY_CODE", "JHB")
        municipality = db.query(Municipality).filter(Municipality.code == municipality_code).first()
        if not municipality:
            municipality = Municipality(
                name=os.getenv("BOOTSTRAP_MUNICIPALITY_NAME", "City of Johannesburg"),
                code=municipality_code,
                region=os.getenv("BOOTSTRAP_MUNICIPALITY_REGION", "Gauteng"),
                province=os.getenv("BOOTSTRAP_MUNICIPALITY_PROVINCE", "Gauteng"),
                contact_person="IT Operations",
                contact_email="it@example.gov",
                is_active=True,
            )
            db.add(municipality)
            db.commit()
            db.refresh(municipality)
        print(f"Municipality ensured: {municipality.code}")

        admin_username = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "admin")
        admin_password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "ChangeMe!123")
        admin_user = db.query(User).filter(User.username == admin_username).first()
        if not admin_user:
            admin_user = User(
                username=admin_username,
                email=os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@watermonitoring.gov"),
                password_hash=get_password_hash(admin_password),
                first_name="System",
                last_name="Administrator",
                is_active=True,
                is_super_admin=True,
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
        if super_admin_role and super_admin_role not in admin_user.roles:
            admin_user.roles.append(super_admin_role)
            db.commit()
        print(f"Super admin ensured: {admin_user.username}")

        sensor_types = [
            SensorType(
                name="Pressure Sensor",
                code="pressure",
                description="Measures water pressure in pipelines",
                unit="bar",
                threshold_config={"min": 2.0, "max": 6.0, "max_rate_of_change": 0.5},
            ),
            SensorType(
                name="Flow Meter",
                code="flow",
                description="Measures water flow rate",
                unit="m3/h",
                threshold_config={"min": 0, "max": 200, "max_rate_of_change": 20},
            ),
            SensorType(
                name="Leak Detector",
                code="leak",
                description="Detects water leakage",
                unit="boolean",
                threshold_config={},
            ),
        ]
        for sensor_type in sensor_types:
            if not db.query(SensorType).filter(SensorType.code == sensor_type.code).first():
                db.add(sensor_type)
        db.commit()
        print("Sensor types ensured.")

        base_settings = [
            SystemSetting(key="system.name", value="National Water Infrastructure Monitoring", is_public=True),
            SystemSetting(key="alerts.cooldown_seconds", value=300, is_public=False),
            SystemSetting(key="sensors.default_sampling_interval", value=60, is_public=False),
        ]
        for setting in base_settings:
            if not db.query(SystemSetting).filter(SystemSetting.key == setting.key, SystemSetting.municipality_id.is_(None)).first():
                db.add(setting)
        db.commit()
        print("System settings ensured.")

        for protocol in ProtocolType:
            if (
                db.query(ProtocolConfiguration)
                .filter(
                    ProtocolConfiguration.protocol == protocol,
                    ProtocolConfiguration.municipality_id.is_(None),
                )
                .first()
                is None
            ):
                db.add(
                    ProtocolConfiguration(
                        protocol=protocol,
                        municipality_id=None,
                        is_enabled=True,
                        settings={},
                    )
                )
        db.commit()
        print("Protocol configurations ensured.")

        print("Database initialization complete.")
        print("Use environment variables BOOTSTRAP_ADMIN_USERNAME / BOOTSTRAP_ADMIN_PASSWORD to customize bootstrap credentials.")
    except Exception as exc:
        db.rollback()
        print(f"Initialization failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
