"""Harden public tables and index phase 4-14 relationships.

Revision ID: 20260918_0006
Revises: 20260918_0005
Create Date: 2026-09-18
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260918_0006"
down_revision: str | None = "20260918_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_circle_members_user_id",
        "circle_members",
        ["user_id"],
    )
    op.create_index(
        "ix_circles_owner_user_id",
        "circles",
        ["owner_user_id"],
    )
    op.create_index(
        "ix_follows_followee_id",
        "follows",
        ["followee_id"],
    )
    op.create_index(
        "ix_movie_list_items_movie_id",
        "movie_list_items",
        ["movie_id"],
    )
    op.create_index(
        "ix_movie_night_candidates_added_by_user_id",
        "movie_night_candidates",
        ["added_by_user_id"],
    )
    op.create_index(
        "ix_movie_night_candidates_movie_id",
        "movie_night_candidates",
        ["movie_id"],
    )
    op.create_index(
        "ix_movie_night_votes_movie_id",
        "movie_night_votes",
        ["movie_id"],
    )
    op.create_index(
        "ix_movie_night_votes_user_id",
        "movie_night_votes",
        ["user_id"],
    )
    op.create_index(
        "ix_movie_nights_circle_id",
        "movie_nights",
        ["circle_id"],
    )
    op.create_index(
        "ix_movie_nights_created_by_user_id",
        "movie_nights",
        ["created_by_user_id"],
    )
    op.create_index(
        "ix_reviews_movie_id",
        "reviews",
        ["movie_id"],
    )
    op.create_index(
        "ix_watch_entries_movie_id",
        "watch_entries",
        ["movie_id"],
    )

    op.execute("ALTER TABLE external_cache ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE alembic_version ENABLE ROW LEVEL SECURITY")

    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
            REVOKE ALL ON TABLE external_cache FROM anon;
            REVOKE ALL ON TABLE alembic_version FROM anon;
          END IF;
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
            REVOKE ALL ON TABLE external_cache FROM authenticated;
            REVOKE ALL ON TABLE alembic_version FROM authenticated;
          END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE alembic_version DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE external_cache DISABLE ROW LEVEL SECURITY")

    op.drop_index("ix_watch_entries_movie_id", table_name="watch_entries")
    op.drop_index("ix_reviews_movie_id", table_name="reviews")
    op.drop_index(
        "ix_movie_nights_created_by_user_id",
        table_name="movie_nights",
    )
    op.drop_index("ix_movie_nights_circle_id", table_name="movie_nights")
    op.drop_index("ix_movie_night_votes_user_id", table_name="movie_night_votes")
    op.drop_index("ix_movie_night_votes_movie_id", table_name="movie_night_votes")
    op.drop_index(
        "ix_movie_night_candidates_movie_id",
        table_name="movie_night_candidates",
    )
    op.drop_index(
        "ix_movie_night_candidates_added_by_user_id",
        table_name="movie_night_candidates",
    )
    op.drop_index("ix_movie_list_items_movie_id", table_name="movie_list_items")
    op.drop_index("ix_follows_followee_id", table_name="follows")
    op.drop_index("ix_circles_owner_user_id", table_name="circles")
    op.drop_index("ix_circle_members_user_id", table_name="circle_members")
