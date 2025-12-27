"""merge_all_heads

Revision ID: b547bd596249
Revises: 01e0725f1aca, 20251212_integrations, 20251212_enhance_timescaledb
Create Date: 2025-12-19 19:04:37.188844

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b547bd596249'
down_revision = ('01e0725f1aca', '20251212_integrations', '20251212_enhance_timescaledb')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

