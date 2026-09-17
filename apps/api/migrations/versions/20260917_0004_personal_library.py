"""Add the private personal movie library.

Revision ID: 20260917_0004
Revises: 20260917_0003
Create Date: 2026-09-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260917_0004"
down_revision: str | None = "20260917_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "movies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tmdb_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("tmdb_id > 0", name="ck_movies_tmdb_id_positive"),
        sa.PrimaryKeyConstraint("id", name="pk_movies"),
        sa.UniqueConstraint("tmdb_id", name="uq_movies_tmdb_id"),
    )
    op.create_table(
        "user_movies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("movie_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default=sa.text("'WATCHLIST'"),
            nullable=False,
        ),
        sa.Column("rating", sa.Numeric(precision=2, scale=1), nullable=True),
        sa.Column("favorite", sa.Boolean(), server_default=sa.text("false"), nullable=False),
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
        sa.CheckConstraint(
            "rating IS NULL OR (rating BETWEEN 0.5 AND 5.0 AND rating * 2 = trunc(rating * 2))",
            name="ck_user_movies_rating_half_steps",
        ),
        sa.CheckConstraint(
            "status IN ('WATCHLIST', 'WATCHED', 'DROPPED')",
            name="ck_user_movies_status",
        ),
        sa.ForeignKeyConstraint(
            ["movie_id"], ["movies.id"], name="fk_user_movies_movie_id_movies", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name="fk_user_movies_user_id_users", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_user_movies"),
        sa.UniqueConstraint("user_id", "movie_id", name="uq_user_movies_user_id_movie_id"),
    )
    op.create_index("ix_user_movies_movie_id", "user_movies", ["movie_id"], unique=False)
    op.create_index(
        "ix_user_movies_user_status_updated_id",
        "user_movies",
        ["user_id", "status", sa.text("updated_at DESC"), "id"],
        unique=False,
    )
    op.create_index(
        "ix_user_movies_user_favorites",
        "user_movies",
        ["user_id"],
        unique=False,
        postgresql_where=sa.text("favorite IS TRUE"),
    )

    op.execute("ALTER TABLE movies ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE user_movies ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
            REVOKE ALL ON TABLE movies, user_movies FROM anon;
          END IF;

          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated')
             AND to_regprocedure('auth.uid()') IS NOT NULL THEN
            REVOKE ALL ON TABLE movies, user_movies FROM authenticated;
            GRANT SELECT ON TABLE movies TO authenticated;
            GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE user_movies TO authenticated;

            CREATE POLICY movies_select_for_owned_library ON movies
              FOR SELECT TO authenticated
              USING (
                EXISTS (
                  SELECT 1 FROM user_movies um
                  JOIN users u ON u.id = um.user_id
                  WHERE um.movie_id = movies.id
                    AND u.auth_user_id = (SELECT auth.uid())
                )
              );
            CREATE POLICY user_movies_select_own ON user_movies
              FOR SELECT TO authenticated
              USING (
                user_id IN (
                  SELECT id FROM users WHERE auth_user_id = (SELECT auth.uid())
                )
              );
            CREATE POLICY user_movies_insert_own ON user_movies
              FOR INSERT TO authenticated
              WITH CHECK (
                user_id IN (
                  SELECT id FROM users WHERE auth_user_id = (SELECT auth.uid())
                )
              );
            CREATE POLICY user_movies_update_own ON user_movies
              FOR UPDATE TO authenticated
              USING (
                user_id IN (
                  SELECT id FROM users WHERE auth_user_id = (SELECT auth.uid())
                )
              )
              WITH CHECK (
                user_id IN (
                  SELECT id FROM users WHERE auth_user_id = (SELECT auth.uid())
                )
              );
            CREATE POLICY user_movies_delete_own ON user_movies
              FOR DELETE TO authenticated
              USING (
                user_id IN (
                  SELECT id FROM users WHERE auth_user_id = (SELECT auth.uid())
                )
              );
          END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.drop_index("ix_user_movies_user_favorites", table_name="user_movies")
    op.drop_index("ix_user_movies_user_status_updated_id", table_name="user_movies")
    op.drop_index("ix_user_movies_movie_id", table_name="user_movies")
    op.drop_table("user_movies")
    op.drop_table("movies")
