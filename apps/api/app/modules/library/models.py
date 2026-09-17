from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Movie(Base):
    __tablename__ = "movies"
    __table_args__ = (CheckConstraint("tmdb_id > 0", name="ck_movies_tmdb_id_positive"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tmdb_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UserMovie(Base):
    __tablename__ = "user_movies"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_user_movies_user_id_movie_id"),
        CheckConstraint(
            "status IN ('WATCHLIST', 'WATCHED', 'DROPPED')",
            name="ck_user_movies_status",
        ),
        CheckConstraint(
            "rating IS NULL OR (rating BETWEEN 0.5 AND 5.0 AND rating * 2 = trunc(rating * 2))",
            name="ck_user_movies_rating_half_steps",
        ),
        Index(
            "ix_user_movies_user_status_updated_id",
            "user_id",
            "status",
            text("updated_at DESC"),
            "id",
        ),
        Index("ix_user_movies_movie_id", "movie_id"),
        Index(
            "ix_user_movies_user_favorites",
            "user_id",
            postgresql_where=text("favorite IS TRUE"),
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    movie_id: Mapped[UUID] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(16), server_default=text("'WATCHLIST'"), nullable=False
    )
    rating: Mapped[Decimal | None] = mapped_column(Numeric(2, 1), nullable=True)
    favorite: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
