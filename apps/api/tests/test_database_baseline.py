from app.core.database import Base


def test_phase_three_metadata_contains_cache_profile_and_private_library() -> None:
    assert set(Base.metadata.tables) == {
        "external_cache",
        "users",
        "movies",
        "user_movies",
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
