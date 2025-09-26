import os
import respx
import httpx
import pytest

OWNER = os.getenv("GITHUB_OWNER", "owner")
REPO  = os.getenv("GITHUB_REPO", "repo")
BASE  = "https://api.github.com"

@pytest.mark.asyncio
@respx.mock
async def test_create_issue_unauthorized_maps_to_401(client):
    route = respx.post(f"{BASE}/repos/{OWNER}/{REPO}/issues").mock(
        return_value=httpx.Response(401, json={"message": "Bad credentials"})
    )
    resp = await client.post("/issues", json={"title": "X"})
    assert route.called
    assert resp.status_code == 401
    data = resp.json()
    # Our handlers wrap errors in detail or body; accept either
    detail = data.get("detail") or data
    assert detail["error"] in ("Unauthorized", "GitHubError")

@pytest.mark.asyncio
@respx.mock
async def test_get_issue_not_found_maps_to_404(client):
    route = respx.get(f"{BASE}/repos/{OWNER}/{REPO}/issues/999999").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )
    resp = await client.get("/issues/999999")
    assert route.called
    assert resp.status_code == 404
