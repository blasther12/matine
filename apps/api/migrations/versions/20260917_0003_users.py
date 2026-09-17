"""Add private user profiles with deny-by-default RLS.

Revision ID: 20260917_0003
Revises: 20260917_0002
Create Date: 2026-09-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260917_0003"
down_revision: str | None = "20260917_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("auth_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(length=30), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("avatar_url", sa.String(length=2048), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("auth_user_id", name="uq_users_auth_user_id"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        DO $$
        BEGIN
          IF to_regclass('auth.users') IS NOT NULL THEN
            ALTER TABLE users
              ADD CONSTRAINT fk_users_auth_user_id_auth_users
              FOREIGN KEY (auth_user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
          END IF;

          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
            REVOKE ALL ON TABLE users FROM anon;
          END IF;

          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated')
             AND to_regprocedure('auth.uid()') IS NOT NULL THEN
            REVOKE ALL ON TABLE users FROM authenticated;
            GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE users TO authenticated;
            CREATE POLICY users_select_own ON users FOR SELECT TO authenticated
              USING ((SELECT auth.uid()) = auth_user_id);
            CREATE POLICY users_insert_own ON users FOR INSERT TO authenticated
              WITH CHECK ((SELECT auth.uid()) = auth_user_id);
            CREATE POLICY users_update_own ON users FOR UPDATE TO authenticated
              USING ((SELECT auth.uid()) = auth_user_id)
              WITH CHECK ((SELECT auth.uid()) = auth_user_id);
            CREATE POLICY users_delete_own ON users FOR DELETE TO authenticated
              USING ((SELECT auth.uid()) = auth_user_id);
          END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.drop_table("users")
