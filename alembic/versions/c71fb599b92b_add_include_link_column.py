"""Add include_link column

Revision ID: c71fb599b92b
Revises: 2de57fa5e865
Create Date: 2022-05-27 19:36:37.967325

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c71fb599b92b"
down_revision = "2de57fa5e865"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column(
            "include_link",
            sa.Boolean(),
            nullable=False,
            server_default=sa.sql.false(),
        ),
    )


def downgrade():
    op.drop_column("user", "include_link")
