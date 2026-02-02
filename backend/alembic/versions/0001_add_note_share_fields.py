"""add note share fields

Revision ID: 0001_add_note_share_fields
Revises: 2f840e72ac66
Create Date: 2026-02-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_add_note_share_fields"
down_revision: Union[str, None] = "2f840e72ac66"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加笔记分享字段。"""
    op.add_column(
        "notes",
        sa.Column("is_shared", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "notes",
        sa.Column("share_uuid", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_notes_share_uuid", "notes", ["share_uuid"], unique=True)


def downgrade() -> None:
    """移除笔记分享字段。"""
    op.drop_index("ix_notes_share_uuid", table_name="notes")
    op.drop_column("notes", "share_uuid")
    op.drop_column("notes", "is_shared")
