"""Initial schema migration for Water Monitoring System

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-02-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema"""
    
    # Municipality table
    op.create_table(
        'municipality',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('location_type', sa.String(50), nullable=False),
        sa.Column('latitude', sa.Float, nullable=True),
        sa.Column('longitude', sa.Float, nullable=True),
        sa.Column('population', sa.Integer, nullable=True),
        sa.Column('water_usage_annual', sa.Float, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_municipality_active', 'municipality', ['is_active'])

    # User table
    op.create_table(
        'user',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('email', sa.String(120), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(256), nullable=False),
        sa.Column('first_name', sa.String(50), nullable=True),
        sa.Column('last_name', sa.String(50), nullable=True),
        sa.Column('municipality_id', sa.Integer, sa.ForeignKey('municipality.id')),
        sa.Column('role', sa.String(50), default='user'),
        sa.Column('is_super_admin', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('last_login', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_user_active', 'user', ['is_active'])
    op.create_index('idx_user_municipality', 'user', ['municipality_id'])

    # Sensor table
    op.create_table(
        'sensor',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('sensor_id', sa.String(100), unique=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('location', sa.String(255), nullable=False),
        sa.Column('sensor_type', sa.String(50), nullable=False),
        sa.Column('measurement_unit', sa.String(20), nullable=False),
        sa.Column('municipality_id', sa.Integer, sa.ForeignKey('municipality.id'), nullable=False),
        sa.Column('latitude', sa.Float, nullable=True),
        sa.Column('longitude', sa.Float, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('last_reading_at', sa.DateTime, nullable=True),
        sa.Column('battery_level', sa.Float, nullable=True),
        sa.Column('signal_strength', sa.Integer, nullable=True),
        sa.Column('firmware_version', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_sensor_active', 'sensor', ['is_active'])
    op.create_index('idx_sensor_municipality', 'sensor', ['municipality_id'])
    op.create_index('idx_sensor_type', 'sensor', ['sensor_type'])

    # Sensor reading table
    op.create_table(
        'sensor_reading',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('sensor_id', sa.Integer, sa.ForeignKey('sensor.id'), nullable=False),
        sa.Column('value', sa.Float, nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    op.create_index('idx_reading_sensor_time', 'sensor_reading', ['sensor_id', 'timestamp'])

    # Alert rules table
    op.create_table(
        'alert_rule',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('sensor_type', sa.String(50), nullable=False),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('threshold_min', sa.Float, nullable=True),
        sa.Column('threshold_max', sa.Float, nullable=True),
        sa.Column('municipality_id', sa.Integer, sa.ForeignKey('municipality.id')),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_alert_rule_active', 'alert_rule', ['is_active'])
    op.create_index('idx_alert_rule_sensor', 'alert_rule', ['sensor_type'])

    # Alert table
    op.create_table(
        'alert',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('alert_rule_id', sa.Integer, sa.ForeignKey('alert_rule.id')),
        sa.Column('sensor_id', sa.Integer, sa.ForeignKey('sensor.id')),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('is_read', sa.Boolean, default=False),
        sa.Column('is_resolved', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_alert_unread', 'alert', ['is_read'])
    op.create_index('idx_alert_severity', 'alert', ['severity'])

    # Incident table
    op.create_table(
        'incident',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('incident_number', sa.String(50), unique=True, nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('municipality_id', sa.Integer, sa.ForeignKey('municipality.id')),
        sa.Column('status', sa.String(20), default='open'),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('assigned_to', sa.Integer, sa.ForeignKey('user.id')),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime, nullable=True),
    )
    op.create_index('idx_incident_status', 'incident', ['status'])
    op.create_index('idx_incident_municipality', 'incident', ['municipality_id'])

    # Device authentication table
    op.create_table(
        'device_auth',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('sensor_id', sa.Integer, sa.ForeignKey('sensor.id')),
        sa.Column('device_id', sa.String(100), unique=True, nullable=False),
        sa.Column('api_key', sa.String(256), unique=True, nullable=True),
        sa.Column('certificate_pem', sa.Text, nullable=True),
        sa.Column('certificate_fingerprint', sa.String(64), nullable=True),
        sa.Column('mqtt_username', sa.String(100), nullable=True),
        sa.Column('mqtt_password_hash', sa.String(256), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('last_authenticated', sa.DateTime, nullable=True),
        sa.Column('expires_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('idx_device_active', 'device_auth', ['is_active'])
    op.create_index('idx_device_sensor', 'device_auth', ['sensor_id'])

    # Audit log table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(100), nullable=True),
        sa.Column('changes', sa.JSON, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), default='success'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    op.create_index('idx_audit_user', 'audit_log', ['user_id'])
    op.create_index('idx_audit_action', 'audit_log', ['action'])
    op.create_index('idx_audit_resource', 'audit_log', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_timestamp', 'audit_log', ['created_at'])


def downgrade() -> None:
    """Drop initial database schema"""
    
    op.drop_index('idx_audit_timestamp')
    op.drop_index('idx_audit_resource')
    op.drop_index('idx_audit_action')
    op.drop_index('idx_audit_user')
    op.drop_table('audit_log')
    
    op.drop_index('idx_device_sensor')
    op.drop_index('idx_device_active')
    op.drop_table('device_auth')
    
    op.drop_index('idx_incident_municipality')
    op.drop_index('idx_incident_status')
    op.drop_table('incident')
    
    op.drop_index('idx_alert_severity')
    op.drop_index('idx_alert_unread')
    op.drop_table('alert')
    
    op.drop_index('idx_alert_rule_sensor')
    op.drop_index('idx_alert_rule_active')
    op.drop_table('alert_rule')
    
    op.drop_index('idx_reading_sensor_time')
    op.drop_table('sensor_reading')
    
    op.drop_index('idx_sensor_type')
    op.drop_index('idx_sensor_municipality')
    op.drop_index('idx_sensor_active')
    op.drop_table('sensor')
    
    op.drop_index('idx_user_municipality')
    op.drop_index('idx_user_active')
    op.drop_table('user')
    
    op.drop_index('idx_municipality_active')
    op.drop_table('municipality')
