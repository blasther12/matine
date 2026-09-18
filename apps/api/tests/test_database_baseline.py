from app.core.database import Base


def test_phase_fifteen_metadata_contains_private_experience_tables() -> None:
    assert set(Base.metadata.tables) == {
        "external_cache",
        "users",
        "movies",
        "user_movies",
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
        "movie_night_vetoes",
        "movie_night_votes",
    }
    columns = set(Base.metadata.tables["external_cache"].columns.keys())
    assert columns == {
        "provider",
        "key",
        "payload",
        "expires_at",
        "created_at",
        "updated_at",
    }
    user_columns = set(Base.metadata.tables["users"].columns.keys())
    assert user_columns == {
        "id",
        "auth_user_id",
        "username",
        "display_name",
        "avatar_url",
        "created_at",
        "updated_at",
    }
    assert "email" not in user_columns
    assert "password" not in user_columns
    movie_columns = set(Base.metadata.tables["movies"].columns.keys())
    assert movie_columns == {"id", "tmdb_id", "created_at"}
    library_columns = set(Base.metadata.tables["user_movies"].columns.keys())
    assert library_columns == {
        "id",
        "user_id",
        "movie_id",
        "status",
        "rating",
        "favorite",
        "created_at",
        "updated_at",
    }
