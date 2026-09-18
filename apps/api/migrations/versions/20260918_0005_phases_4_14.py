"""Add phases 4-14 private experience data.

Revision ID: 20260918_0005
Revises: 20260917_0004
Create Date: 2026-09-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260918_0005"
down_revision: str | None = "20260917_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid() -> sa.Column:
    return sa.Column(
        "id",
        postgresql.UUID(as_uuid=True),
        server_default=sa.text("gen_random_uuid()"),
        nullable=False,
    )


def upgrade() -> None:
    op.create_table(
        "watch_entries",
        _uuid(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("movie_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("watched_at", sa.Date(), nullable=False),
        sa.Column("rewatch", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_watch_entries_user_watched_at",
        "watch_entries",
        ["user_id", sa.text("watched_at DESC")],
    )

    op.create_table(
        "reviews",
        _uuid(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("movie_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("spoiler", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "visibility",
            sa.String(length=16),
            server_default=sa.text("'PRIVATE'"),
            nullable=False,
        ),
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
            "visibility IN ('PRIVATE', 'FOLLOWERS', 'PUBLIC')",
            name="ck_reviews_visibility",
        ),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "movie_id", name="uq_reviews_user_movie"),
    )
    op.create_index(
        "ix_reviews_visibility_created_at",
        "reviews",
        ["visibility", sa.text("created_at DESC")],
    )

    op.create_table(
        "movie_lists",
        _uuid(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column(
            "visibility",
            sa.String(length=16),
            server_default=sa.text("'PRIVATE'"),
            nullable=False,
        ),
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
            "visibility IN ('PRIVATE', 'PUBLIC')",
            name="ck_movie_lists_visibility",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_movie_lists_user_updated_at",
        "movie_lists",
        ["user_id", sa.text("updated_at DESC")],
    )

    op.create_table(
        "movie_list_items",
        _uuid(),
        sa.Column("list_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("movie_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("position >= 0", name="ck_movie_list_items_position"),
        sa.ForeignKeyConstraint(["list_id"], ["movie_lists.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "list_id", "movie_id", name="uq_movie_list_items_list_movie"
        ),
        sa.UniqueConstraint(
            "list_id", "position", name="uq_movie_list_items_list_position"
        ),
    )

    op.create_table(
        "follows",
        sa.Column("follower_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("followee_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("follower_id <> followee_id", name="ck_follows_not_self"),
        sa.ForeignKeyConstraint(["followee_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["follower_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("follower_id", "followee_id"),
    )

    op.create_table(
        "streaming_preferences",
        _uuid(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider_name", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "provider_name",
            name="uq_streaming_preferences_user_provider",
        ),
    )

    op.create_table(
        "circles",
        _uuid(),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "circle_members",
        sa.Column("circle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('OWNER', 'MEMBER')", name="ck_circle_members_role"
        ),
        sa.ForeignKeyConstraint(["circle_id"], ["circles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("circle_id", "user_id"),
    )

    op.create_table(
        "movie_nights",
        _uuid(),
        sa.Column("circle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default=sa.text("'OPEN'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('OPEN', 'CLOSED')", name="ck_movie_nights_status"
        ),
        sa.ForeignKeyConstraint(["circle_id"], ["circles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "movie_night_candidates",
        sa.Column("night_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("movie_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "added_by_user_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["night_id"], ["movie_nights.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["added_by_user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("night_id", "movie_id"),
    )

    op.create_table(
        "movie_night_votes",
        _uuid(),
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
        sa.ForeignKeyConstraint(["movie_id"], ["movies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "night_id", "user_id", name="uq_movie_night_votes_night_user"
        ),
    )

    private_tables = (
        "watch_entries",
        "reviews",
        "movie_lists",
        "movie_list_items",
        "follows",
        "streaming_preferences",
        "circles",
        "circle_members",
        "movie_nights",
        "movie_night_candidates",
        "movie_night_votes",
    )
    for table in private_tables:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')

    op.execute(
        """
        DO $$
        DECLARE
          table_name text;
        BEGIN
          FOREACH table_name IN ARRAY ARRAY[
            'watch_entries','reviews','movie_lists','movie_list_items','follows',
            'streaming_preferences','circles','circle_members','movie_nights',
            'movie_night_candidates','movie_night_votes'
          ]
          LOOP
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
              EXECUTE format('REVOKE ALL ON TABLE %I FROM anon', table_name);
            END IF;
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
              EXECUTE format('REVOKE ALL ON TABLE %I FROM authenticated', table_name);
            END IF;
          END LOOP;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.drop_table("movie_night_votes")
    op.drop_table("movie_night_candidates")
    op.drop_table("movie_nights")
    op.drop_table("circle_members")
    op.drop_table("circles")
    op.drop_table("streaming_preferences")
    op.drop_table("follows")
    op.drop_table("movie_list_items")
    op.drop_index("ix_movie_lists_user_updated_at", table_name="movie_lists")
    op.drop_table("movie_lists")
    op.drop_index("ix_reviews_visibility_created_at", table_name="reviews")
    op.drop_table("reviews")
    op.drop_index("ix_watch_entries_user_watched_at", table_name="watch_entries")
    op.drop_table("watch_entries")
