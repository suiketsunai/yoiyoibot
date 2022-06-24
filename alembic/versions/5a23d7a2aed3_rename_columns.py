"""Rename columns

Revision ID: 5a23d7a2aed3
Revises: c71fb599b92b
Create Date: 2022-06-24 19:35:28.588437

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5a23d7a2aed3"
down_revision = "c71fb599b92b"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("user", "full_name", new_column_name="name")
    op.alter_column("user", "nick_name", new_column_name="chat_link")


def downgrade():
    op.alter_column("user", "name", new_column_name="full_name")
    op.alter_column("user", "chat_link", new_column_name="nick_name")
