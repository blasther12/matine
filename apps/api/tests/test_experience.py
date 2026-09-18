import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.modules.experience.schemas import (
    DiaryCreate,
    MovieListCreate,
    MovieNightCreate,
    MovieNightVetoCreate,
    ReviewUpsert,
    StreamingPreferences,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/me/diary",
        "/me/reviews",
        "/me/lists",
        "/social/feed",
        "/me/streaming",
        "/me/circles",
        "/me/circles/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/streaming",
        "/me/recommendations",
        "/me/stats",
        "/me/wrapped?year=2026",
    ],
)
async def test_phase_4_14_routes_require_authentication(client: AsyncClient, path: str) -> None:
    response = await client.get(path)

    assert response.status_code == 401
    assert response.json()["error"] == "authentication_required"


def test_private_content_defaults_to_private() -> None:
    review = ReviewUpsert(tmdb_id=550, body="Ótimo filme")
    movie_list = MovieListCreate(name="Favoritos")

    assert review.visibility == "PRIVATE"
    assert movie_list.visibility == "PRIVATE"


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (
            DiaryCreate,
            {
                "tmdb_id": 550,
                "watched_at": "2026-09-18",
                "user_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            },
        ),
        (
            ReviewUpsert,
            {
                "tmdb_id": 550,
                "body": "texto",
                "user_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            },
        ),
        (
            MovieListCreate,
            {
                "name": "lista",
                "user_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            },
        ),
    ],
)
def test_private_phase_payloads_reject_client_ownership(
    model: type[object], payload: dict[str, object]
) -> None:
    with pytest.raises(ValidationError):
        model.model_validate(payload)  # type: ignore[attr-defined]


def test_streaming_preferences_are_minimized_and_deduplicated() -> None:
    value = StreamingPreferences(providers=[" Netflix ", "netflix", "", "Prime Video"])

    assert value.providers == ["Netflix", "Prime Video"]


def test_movie_night_context_is_normalized_and_bounded() -> None:
    value = MovieNightCreate(
        title="Sexta de terror",
        max_runtime_minutes=120,
        preferred_genres=[" Terror ", "terror", "Suspense"],
    )

    assert value.max_runtime_minutes == 120
    assert value.preferred_genres == ["Terror", "Suspense"]

    with pytest.raises(ValidationError):
        MovieNightCreate(title="Longa demais", max_runtime_minutes=900)


def test_private_veto_payload_never_accepts_client_ownership() -> None:
    with pytest.raises(ValidationError):
        MovieNightVetoCreate.model_validate(
            {
                "tmdb_id": 550,
                "user_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            }
        )
