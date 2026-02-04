"""add ledger note fields

Revision ID: 0007_add_note_ledger_fields
Revises: 0006_add_ledger_summary
Create Date: 2026-02-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0007_add_note_ledger_fields"
down_revision = "0006_add_ledger_summary"
branch_labels = None
depends_on = None


def upgrade():
    """Add ledger note markers to notes table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if "notes" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("notes")}
    if "is_ledger_note" not in existing_columns:
        op.add_column("notes", sa.Column("is_ledger_note", sa.Boolean(), nullable=False, server_default=sa.false()))
    if "ledger_month" not in existing_columns:
        op.add_column("notes", sa.Column("ledger_month", sa.String(length=7), nullable=True))
    op.alter_column("notes", "is_ledger_note", server_default=None)


def downgrade():
    """Remove ledger note markers from notes table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if "notes" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("notes")}
    if "ledger_month" in existing_columns:
        op.drop_column("notes", "ledger_month")
    if "is_ledger_note" in existing_columns:
        op.drop_column("notes", "is_ledger_note")
