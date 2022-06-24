"""Rename User table to Chat

Revision ID: 0bdf085f57f6
Revises: 5a23d7a2aed3
Create Date: 2022-06-24 19:41:18.674287

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0bdf085f57f6"
down_revision = "5a23d7a2aed3"
branch_labels = None
depends_on = None


def upgrade():
    op.rename_table("user", "chat")
    op.execute("ALTER INDEX user_pkey RENAME TO chat_pkey")


def downgrade():
    op.rename_table("chat", "user")
    op.execute("ALTER INDEX chat_pkey RENAME TO user_pkey")
