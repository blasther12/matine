"""Add group decision context and private vetoes.

Revision ID: 20260918_0007
Revises: 20260918_0006
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260918_0007"
down_revision: str | None = "20260918_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "movie_nights",
        sa.Column("max_runtime_minutes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "movie_nights",
        sa.Column(
            "preferred_genres",
            sa.String(length=300),
            server_default=sa.text("''"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_movie_nights_max_runtime",
        "movie_nights",
        "max_runtime_minutes IS NULL OR (max_runtime_minutes >= 30 AND max_runtime_minutes <= 600)",
    )

    op.create_table(
        "movie_night_vetoes",
        sa.Column("night_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("movie_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["night_id"], ["movie_nights.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("night_id", "user_id", "movie_id"),
    )
    op.create_index(
        "ix_movie_night_vetoes_user_id",
        "movie_night_vetoes",
        ["user_id"],
    )
    op.create_index(
        "ix_movie_night_vetoes_movie_id",
        "movie_night_vetoes",
        ["movie_id"],
    )

    op.execute("ALTER TABLE movie_night_vetoes ENABLE ROW LEVEL SECURITY")
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
            REVOKE ALL ON TABLE movie_night_vetoes FROM anon;
          END IF;
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
            REVOKE ALL ON TABLE movie_night_vetoes FROM authenticated;
          END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_movie_night_vetoes_movie_id",
        table_name="movie_night_vetoes",
    )
    op.drop_index(
        "ix_movie_night_vetoes_user_id",
        table_name="movie_night_vetoes",
    )
    op.drop_table("movie_night_vetoes")
    op.drop_constraint(
        "ck_movie_nights_max_runtime",
        "movie_nights",
        type_="check",
    )
    op.drop_column("movie_nights", "preferred_genres")
    op.drop_column("movie_nights", "max_runtime_minutes")
