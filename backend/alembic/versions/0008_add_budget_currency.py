"""add currency to ledger budgets

Revision ID: 0008_add_budget_currency
Revises: 0007_add_note_ledger_fields
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0008_add_budget_currency"
down_revision = "0007_add_note_ledger_fields"
branch_labels = None
depends_on = None


def upgrade():
    """Add currency column to ledger budgets."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if "ledger_budgets" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("ledger_budgets")}
    if "currency" not in existing_columns:
        op.add_column(
            "ledger_budgets",
            sa.Column("currency", sa.String(length=16), nullable=False, server_default="CNY"),
        )
        op.alter_column("ledger_budgets", "currency", server_default=None)


def downgrade():
    """Remove currency column from ledger budgets."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if "ledger_budgets" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("ledger_budgets")}
    if "currency" in existing_columns:
        op.drop_column("ledger_budgets", "currency")
