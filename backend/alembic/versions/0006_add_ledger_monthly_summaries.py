"""add ledger monthly summaries

Revision ID: 0006_add_ledger_summary
Revises: 0005_add_ledger_budgets
Create Date: 2026-02-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0006_add_ledger_summary"
down_revision = "0005_add_ledger_budgets"
branch_labels = None
depends_on = None


def upgrade():
    """Create ledger monthly summaries table."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if "ledger_monthly_summaries" in inspector.get_table_names():
        return
    op.create_table(
        "ledger_monthly_summaries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("month", sa.String(length=7), nullable=False, index=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("last_entry_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("user_id", "month", name="uq_ledger_summary_user_month"),
    )


def downgrade():
    """Drop ledger monthly summaries table."""
    op.drop_table("ledger_monthly_summaries")
