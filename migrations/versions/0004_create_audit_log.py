"""create audit log table

Revision ID: 0004_create_audit_log
Revises: 0003_extend_user_sessions
Create Date: 2026-05-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "0004_create_audit_log"
down_revision: Union[str, Sequence[str], None] = "0003_extend_user_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auditlog",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=False),
        sa.Column("action", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("ip_address", sqlmodel.sql.sqltypes.AutoString(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["target_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_auditlog_actor_id"), "auditlog", ["actor_id"], unique=False)
    op.create_index(op.f("ix_auditlog_target_user_id"), "auditlog", ["target_user_id"], unique=False)
    op.create_index(op.f("ix_auditlog_action"), "auditlog", ["action"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_auditlog_action"), table_name="auditlog")
    op.drop_index(op.f("ix_auditlog_target_user_id"), table_name="auditlog")
    op.drop_index(op.f("ix_auditlog_actor_id"), table_name="auditlog")
    op.drop_table("auditlog")
