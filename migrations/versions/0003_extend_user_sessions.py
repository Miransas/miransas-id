"""extend user sessions with family, metadata and revocation fields

Revision ID: 0003_extend_user_sessions
Revises: 0002_create_user_sessions_table
Create Date: 2026-05-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0003_extend_user_sessions"
down_revision: Union[str, Sequence[str], None] = "0002_create_user_sessions_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # family_id — NOT NULL; existing rows (if any) get an empty-string sentinel
    # so the migration does not break. Production should have no rows at this point.
    op.add_column(
        "usersession",
        sa.Column(
            "family_id",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
            server_default="",
        ),
    )
    op.create_index(op.f("ix_usersession_family_id"), "usersession", ["family_id"], unique=False)

    op.add_column(
        "usersession",
        sa.Column("replaced_by_session_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "usersession",
        sa.Column("user_agent", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
    )
    op.add_column(
        "usersession",
        sa.Column("ip_address", sqlmodel.sql.sqltypes.AutoString(length=45), nullable=True),
    )
    op.add_column(
        "usersession",
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "usersession",
        sa.Column("revocation_reason", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("usersession", "revocation_reason")
    op.drop_column("usersession", "last_used_at")
    op.drop_column("usersession", "ip_address")
    op.drop_column("usersession", "user_agent")
    op.drop_column("usersession", "replaced_by_session_id")
    op.drop_index(op.f("ix_usersession_family_id"), table_name="usersession")
    op.drop_column("usersession", "family_id")
