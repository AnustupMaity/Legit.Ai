"""initial

Revision ID: 0001
Revises: 
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # This migration is intentionally minimal. Run `alembic revision --autogenerate -m "initial"`
    pass


def downgrade():
    pass
