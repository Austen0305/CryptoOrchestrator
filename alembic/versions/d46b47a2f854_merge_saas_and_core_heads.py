"""merge saas and core heads

Revision ID: d46b47a2f854
Revises: 001_initial_saas, b2c3d4e5f6a7
Create Date: 2025-11-28 21:12:11.038433

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd46b47a2f854'
down_revision = ('001_initial_saas', 'b2c3d4e5f6a7')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

