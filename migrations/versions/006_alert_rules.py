"""Add alert rule table for threshold alerting

Revision ID: 006_alert_rules
Revises: 005_audit_events
Create Date: 2026-03-17 10:15:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_alert_rules'
down_revision = '005_audit_events'
branch_labels = None
depends_on = None


def upgrade():
    """Create tenant-scoped alert rule table."""
    op.create_table(
        'alert_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('metric', sa.String(length=64), nullable=False),
        sa.Column('operator', sa.String(length=2), nullable=False),
        sa.Column('threshold', sa.Float(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'name', name='uq_alert_rules_org_name'),
    )

    op.create_index('ix_alert_rules_organization_id', 'alert_rules', ['organization_id'], unique=False)


def downgrade():
    """Drop alert rule table."""
    op.drop_index('ix_alert_rules_organization_id', table_name='alert_rules')
    op.drop_table('alert_rules')
