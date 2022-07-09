"""Add tw_style column

Revision ID: b5115239219d
Revises: d461dd6281a5
Create Date: 2022-07-09 21:02:49.897227

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b5115239219d"
down_revision = "d461dd6281a5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "chat",
        sa.Column(
            "tw_style",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade():
    op.drop_column("chat", "tw_style")
