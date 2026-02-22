"""Add webhook tables

Revision ID: add_webhook_tables
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_webhook_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('municipality_id', sa.String(36), sa.ForeignKey('municipalities.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('secret', sa.String(100), nullable=False),
        sa.Column('events', sa.JSON, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create webhook_deliveries table
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('webhook_id', sa.String(36), sa.ForeignKey('webhooks.id'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('payload', sa.JSON, nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('response_code', sa.Integer),
        sa.Column('response_body', sa.Text),
        sa.Column('error_message', sa.Text),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('delivered_at', sa.DateTime)
    )
    
    # Create indexes
    op.create_index('idx_webhooks_municipality', 'webhooks', ['municipality_id'])
    op.create_index('idx_webhook_deliveries_webhook', 'webhook_deliveries', ['webhook_id'])
    op.create_index('idx_webhook_deliveries_status', 'webhook_deliveries', ['status'])


def downgrade():
    op.drop_index('idx_webhook_deliveries_status', 'webhook_deliveries')
    op.drop_index('idx_webhook_deliveries_webhook', 'webhook_deliveries')
    op.drop_index('idx_webhooks_municipality', 'webhooks')
    op.drop_table('webhook_deliveries')
    op.drop_table('webhooks')
