"""add tenant_id to detections and add roles tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    # Add tenant_id to detections
    try:
        op.add_column('detections', sa.Column('tenant_id', sa.Integer(), nullable=False, server_default='0'))
    except Exception:
        # Column may already exist
        pass

    # Add columns to refresh_tokens
    try:
        op.add_column('refresh_tokens', sa.Column('ip_address', sa.String(length=64), nullable=True))
        op.add_column('refresh_tokens', sa.Column('user_agent', sa.String(length=512), nullable=True))
        op.add_column('refresh_tokens', sa.Column('last_used_at', sa.String(length=32), nullable=True))
    except Exception:
        pass

    # Create roles table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=64), nullable=False, unique=True),
    )

    # Create user_roles table
    op.create_table(
        'user_roles',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('role_id', sa.Integer(), nullable=False, index=True),
    )


def downgrade():
    try:
        op.drop_table('user_roles')
    except Exception:
        pass
    try:
        op.drop_table('roles')
    except Exception:
        pass
    try:
        op.drop_column('refresh_tokens', 'last_used_at')
        op.drop_column('refresh_tokens', 'user_agent')
        op.drop_column('refresh_tokens', 'ip_address')
    except Exception:
        pass
    try:
        op.drop_column('detections', 'tenant_id')
    except Exception:
        pass
