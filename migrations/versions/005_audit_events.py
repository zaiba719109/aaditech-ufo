"""Add persistent audit event table

Revision ID: 005_audit_events
Revises: 004_jwt_revoked_tokens
Create Date: 2026-03-16 23:55:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_audit_events'
down_revision = '004_jwt_revoked_tokens'
branch_labels = None
depends_on = None


def upgrade():
    """Create table for persistent audit/compliance events."""
    op.create_table(
        'audit_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('action', sa.String(length=120), nullable=False),
        sa.Column('outcome', sa.String(length=20), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('method', sa.String(length=10), nullable=True),
        sa.Column('path', sa.String(length=255), nullable=True),
        sa.Column('remote_addr', sa.String(length=64), nullable=True),
        sa.Column('event_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_audit_events_created_at', 'audit_events', ['created_at'], unique=False)
    op.create_index('ix_audit_events_action', 'audit_events', ['action'], unique=False)
    op.create_index('ix_audit_events_outcome', 'audit_events', ['outcome'], unique=False)
    op.create_index('ix_audit_events_tenant_id', 'audit_events', ['tenant_id'], unique=False)
    op.create_index('ix_audit_events_user_id', 'audit_events', ['user_id'], unique=False)


def downgrade():
    """Drop audit event persistence table."""
    op.drop_index('ix_audit_events_user_id', table_name='audit_events')
    op.drop_index('ix_audit_events_tenant_id', table_name='audit_events')
    op.drop_index('ix_audit_events_outcome', table_name='audit_events')
    op.drop_index('ix_audit_events_action', table_name='audit_events')
    op.drop_index('ix_audit_events_created_at', table_name='audit_events')
    op.drop_table('audit_events')
