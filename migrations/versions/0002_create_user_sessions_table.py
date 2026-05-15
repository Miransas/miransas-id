"""create user sessions table

Revision ID: 0002_create_user_sessions_table
Revises: 0001_create_users_table
Create Date: 2026-05-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "0002_create_user_sessions_table"
down_revision: Union[str, Sequence[str], None] = "0001_create_users_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usersession",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("refresh_token_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("refresh_token_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_usersession_user_id"), "usersession", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_usersession_refresh_token_hash"),
        "usersession",
        ["refresh_token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_usersession_refresh_token_id"),
        "usersession",
        ["refresh_token_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_usersession_refresh_token_id"), table_name="usersession")
    op.drop_index(op.f("ix_usersession_refresh_token_hash"), table_name="usersession")
    op.drop_index(op.f("ix_usersession_user_id"), table_name="usersession")
    op.drop_table("usersession")
