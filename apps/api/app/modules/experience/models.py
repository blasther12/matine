from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WatchEntry(Base):
    __tablename__ = "watch_entries"
    __table_args__ = (
        Index("ix_watch_entries_user_watched_at", "user_id", text("watched_at DESC")),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[UUID] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    watched_at: Mapped[date] = mapped_column(Date, nullable=False)
    rewatch: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_reviews_user_movie"),
        CheckConstraint(
            "visibility IN ('PRIVATE', 'FOLLOWERS', 'PUBLIC')",
            name="ck_reviews_visibility",
        ),
        Index("ix_reviews_visibility_created_at", "visibility", text("created_at DESC")),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[UUID] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    spoiler: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)
    visibility: Mapped[str] = mapped_column(
        String(16), server_default=text("'PRIVATE'"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MovieList(Base):
    __tablename__ = "movie_lists"
    __table_args__ = (
        CheckConstraint(
            "visibility IN ('PRIVATE', 'PUBLIC')", name="ck_movie_lists_visibility"
        ),
        Index("ix_movie_lists_user_updated_at", "user_id", text("updated_at DESC")),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    visibility: Mapped[str] = mapped_column(
        String(16), server_default=text("'PRIVATE'"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MovieListItem(Base):
    __tablename__ = "movie_list_items"
    __table_args__ = (
        UniqueConstraint("list_id", "movie_id", name="uq_movie_list_items_list_movie"),
        UniqueConstraint("list_id", "position", name="uq_movie_list_items_list_position"),
        CheckConstraint("position >= 0", name="ck_movie_list_items_position"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    list_id: Mapped[UUID] = mapped_column(
        ForeignKey("movie_lists.id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[UUID] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (
        CheckConstraint("follower_id <> followee_id", name="ck_follows_not_self"),
    )

    follower_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    followee_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StreamingPreference(Base):
    __tablename__ = "streaming_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "provider_name", name="uq_streaming_preferences_user_provider"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider_name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Circle(Base):
    __tablename__ = "circles"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CircleMember(Base):
    __tablename__ = "circle_members"
    __table_args__ = (
        CheckConstraint("role IN ('OWNER', 'MEMBER')", name="ck_circle_members_role"),
    )

    circle_id: Mapped[UUID] = mapped_column(
        ForeignKey("circles.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MovieNight(Base):
    __tablename__ = "movie_nights"
    __table_args__ = (
        CheckConstraint(
            "status IN ('OPEN', 'CLOSED')", name="ck_movie_nights_status"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    circle_id: Mapped[UUID] = mapped_column(
        ForeignKey("circles.id", ondelete="CASCADE"), nullable=False
    )
    created_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), server_default=text("'OPEN'"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MovieNightCandidate(Base):
    __tablename__ = "movie_night_candidates"

    night_id: Mapped[UUID] = mapped_column(
        ForeignKey("movie_nights.id", ondelete="CASCADE"), primary_key=True
    )
    movie_id: Mapped[UUID] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    added_by_user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MovieNightVote(Base):
    __tablename__ = "movie_night_votes"
    __table_args__ = (
        UniqueConstraint("night_id", "user_id", name="uq_movie_night_votes_night_user"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    night_id: Mapped[UUID] = mapped_column(
        ForeignKey("movie_nights.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[UUID] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
