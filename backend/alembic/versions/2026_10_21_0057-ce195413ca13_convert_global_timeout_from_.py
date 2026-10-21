"""convert global timeout from milliseconds to seconds

Revision ID: ce195413ca13
Revises: 9c921bfc56e6
Create Date: 2026-10-21 00:57:38.937217

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ce195413ca13"
down_revision: Union[str, Sequence[str], None] = "9c921bfc56e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    global_config = sa.table(
        "ferron_global_config",
        sa.column("timeout", sa.Integer),
    )

    seconds = sa.func.round(global_config.c.timeout / 1000.0)
    new_timeout = sa.case(
        (global_config.c.timeout <= 0, 0),
        (seconds < 1, 1),
        else_=sa.cast(seconds, sa.Integer),
    )

    op.execute(global_config.update().values(timeout=new_timeout))


def downgrade() -> None:
    """Downgrade schema."""
    raise RuntimeError("Downgrades are not supported. Restore from backup.")
