"""add todo ai flag

Revision ID: 0002_add_todo_ai_flag
Revises: 0001_add_note_share_fields
Create Date: 2026-02-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002_add_todo_ai_flag"
down_revision: Union[str, None] = "0001_add_note_share_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "todos",
        sa.Column("is_ai_generated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("todos", "is_ai_generated")
