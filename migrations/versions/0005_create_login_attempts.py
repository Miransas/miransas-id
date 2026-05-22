"""create login attempts table

Revision ID: 0005_create_login_attempts
Revises: 0004_create_audit_log
Create Date: 2026-05-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0005_create_login_attempts"
down_revision: Union[str, Sequence[str], None] = "0004_create_audit_log"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "loginattempt",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "username_or_email",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column(
            "ip_address",
            sqlmodel.sql.sqltypes.AutoString(length=45),
            nullable=True,
        ),
        sa.Column(
            "user_agent",
            sqlmodel.sql.sqltypes.AutoString(length=500),
            nullable=True,
        ),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column(
            "failure_reason",
            sqlmodel.sql.sqltypes.AutoString(length=50),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_loginattempt_username_or_email"),
        "loginattempt",
        ["username_or_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_loginattempt_ip_address"),
        "loginattempt",
        ["ip_address"],
        unique=False,
    )
    op.create_index(
        op.f("ix_loginattempt_success"),
        "loginattempt",
        ["success"],
        unique=False,
    )
    op.create_index(
        op.f("ix_loginattempt_created_at"),
        "loginattempt",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_loginattempt_created_at"), table_name="loginattempt")
    op.drop_index(op.f("ix_loginattempt_success"), table_name="loginattempt")
    op.drop_index(op.f("ix_loginattempt_ip_address"), table_name="loginattempt")
    op.drop_index(op.f("ix_loginattempt_username_or_email"), table_name="loginattempt")
    op.drop_table("loginattempt")
