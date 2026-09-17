import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_response_is_exact(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.content == b'{"status":"ok"}'
    assert response.json() == {"status": "ok"}
    assert response.headers["content-type"] == "application/json"
    assert "database" not in response.text
    assert "version" not in response.text
