"""Rename last_link to last_info

Revision ID: d461dd6281a5
Revises: 08cccf6bbe79
Create Date: 2022-06-24 20:15:55.176420

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d461dd6281a5"
down_revision = "08cccf6bbe79"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("chat", "last_link", new_column_name="last_info")


def downgrade():
    op.alter_column("chat", "last_info", new_column_name="last_link")
