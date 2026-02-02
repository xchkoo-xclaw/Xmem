"""add note ai summary

Revision ID: 0003_add_note_ai_summary
Revises: 0002_add_todo_ai_flag
Create Date: 2026-02-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_add_note_ai_summary"
down_revision: Union[str, None] = "0002_add_todo_ai_flag"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("notes", sa.Column("ai_summary", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("notes", "ai_summary")
