"""Convert datetime columns to TIMESTAMPTZ

Revision ID: 0006_datetime_tz
Revises: 0005_create_login_attempts
Create Date: 2026-05-23

"""
from alembic import op


revision = "0006_datetime_tz"
down_revision = "0005_create_login_attempts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # User
    op.execute("ALTER TABLE \"user\" ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';")
    op.execute("ALTER TABLE \"user\" ALTER COLUMN last_login TYPE TIMESTAMPTZ USING last_login AT TIME ZONE 'UTC';")

    # UserSession
    op.execute("ALTER TABLE usersession ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';")
    op.execute("ALTER TABLE usersession ALTER COLUMN expires_at TYPE TIMESTAMPTZ USING expires_at AT TIME ZONE 'UTC';")
    op.execute("ALTER TABLE usersession ALTER COLUMN revoked_at TYPE TIMESTAMPTZ USING revoked_at AT TIME ZONE 'UTC';")
    op.execute("ALTER TABLE usersession ALTER COLUMN last_used_at TYPE TIMESTAMPTZ USING last_used_at AT TIME ZONE 'UTC';")

    # AuditLog
    op.execute("ALTER TABLE auditlog ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';")

    # LoginAttempt
    op.execute("ALTER TABLE loginattempt ALTER COLUMN created_at TYPE TIMESTAMPTZ USING created_at AT TIME ZONE 'UTC';")


def downgrade() -> None:
    op.execute("ALTER TABLE loginattempt ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE auditlog ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE usersession ALTER COLUMN last_used_at TYPE TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE usersession ALTER COLUMN revoked_at TYPE TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE usersession ALTER COLUMN expires_at TYPE TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE usersession ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE \"user\" ALTER COLUMN last_login TYPE TIMESTAMP WITHOUT TIME ZONE;")
    op.execute("ALTER TABLE \"user\" ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE;")
