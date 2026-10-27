"""convert load balancer health check window from milliseconds to seconds

Revision ID: bd1bc00210d4
Revises: ce195413ca13
Create Date: 2026-10-27 21:33:42.494983

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bd1bc00210d4"
down_revision: Union[str, Sequence[str], None] = "ce195413ca13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    load_balancer_config = sa.table(
        "ferron_load_balancer_config",
        sa.column("lb_health_check_window", sa.Integer),
    )

    seconds = sa.func.round(load_balancer_config.c.lb_health_check_window / 1000.0)
    new_window = sa.case(
        (load_balancer_config.c.lb_health_check_window <= 0, 0),
        (seconds < 1, 1),
        else_=sa.cast(seconds, sa.Integer),
    )

    op.execute(load_balancer_config.update().values(lb_health_check_window=new_window))


def downgrade() -> None:
    """Downgrade schema."""
    raise RuntimeError("Downgrades are not supported. Restore from backup.")
