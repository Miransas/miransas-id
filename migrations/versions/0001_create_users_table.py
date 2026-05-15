"""create users table

Revision ID: 0001_create_users_table
Revises:
Create Date: 2026-05-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "0001_create_users_table"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("username", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("full_name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column(
            "rank",
            sa.Enum("Novice", "Architect", "Elite", "Core Developer", name="miransasrank"),
            nullable=False,
        ),
        sa.Column("badges", sa.JSON(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hashed_password", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
    op.create_index(op.f("ix_user_username"), "user", ["username"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_username"), table_name="user")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
