"""baseline

Revision ID: 2f840e72ac66
Revises: None
Create Date: 2026-02-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f840e72ac66"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """占位基线迁移，用于对齐既有数据库版本。"""
    pass


def downgrade() -> None:
    """占位基线迁移回滚。"""
    pass
