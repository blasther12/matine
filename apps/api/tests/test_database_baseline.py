from app.core.database import Base


def test_phase_two_metadata_contains_cache_and_private_user_profile() -> None:
    assert set(Base.metadata.tables) == {"external_cache", "users"}
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
