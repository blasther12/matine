from app.core.database import Base


def test_phase_one_metadata_contains_only_public_external_cache() -> None:
    assert set(Base.metadata.tables) == {"external_cache"}
    columns = set(Base.metadata.tables["external_cache"].columns.keys())
    assert columns == {
        "provider",
        "key",
        "payload",
        "expires_at",
        "created_at",
        "updated_at",
    }
