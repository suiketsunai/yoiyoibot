"""Create table User

Revision ID: 2de57fa5e865
Revises: 
Create Date: 2022-03-27 04:32:04.184196

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2de57fa5e865"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("full_name", sa.String(), nullable=True),
        sa.Column("nick_name", sa.String(), nullable=True),
        sa.Column("last_link", sa.String(), nullable=True),
        sa.Column("tw_orig", sa.Boolean(), nullable=False),
        sa.Column("tt_orig", sa.Boolean(), nullable=False),
        sa.Column("in_orig", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("user")
