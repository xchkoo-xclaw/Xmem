"""add ledger budgets

Revision ID: 0005_add_ledger_budgets
Revises: 0004_add_export_jobs
Create Date: 2026-02-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0005_add_ledger_budgets"
down_revision = "0004_add_export_jobs"
branch_labels = None
depends_on = None


def upgrade():
    """Create ledger budgets table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if "ledger_budgets" in inspector.get_table_names():
        return
    op.create_table(
        "ledger_budgets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("month", sa.String(length=7), nullable=False, index=True),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "month", name="uq_ledger_budget_user_month"),
    )


def downgrade():
    """Drop ledger budgets table."""
    op.drop_table("ledger_budgets")
