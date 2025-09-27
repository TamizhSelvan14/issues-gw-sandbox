### Coded by - Jaya Vyas - SJSUID- 019144463 #####
# File: tests/test_github_errors.py
# Purpose: Verify my gateway maps GitHub API errors (401, 404, etc.)
# into consistent FastAPI responses. I use respx to mock httpx calls.

import os
import respx
import httpx
import pytest

# Defaults to "owner/repo" if not provided via env.
OWNER = os.getenv("GITHUB_OWNER", "owner")
REPO  = os.getenv("GITHUB_REPO", "repo")
BASE  = "https://api.github.com"

@pytest.mark.asyncio
@respx.mock
async def test_create_issue_unauthorized_maps_to_401(client):
    """
    Scenario: GitHub returns 401 Unauthorized when creating an issue.
    Expectation: My /issues POST maps that upstream 401 into a structured
    401 response with error = Unauthorized or GitHubError.
    """
    # I mock the GitHub /issues POST endpoint with a 401 response.
    route = respx.post(f"{BASE}/repos/{OWNER}/{REPO}/issues").mock(
        return_value=httpx.Response(401, json={"message": "Bad credentials"})
    )

    # Call my gateway’s endpoint.
    resp = await client.post("/issues", json={"title": "X"})

    # Ensure the mocked GitHub route was hit.
    assert route.called
    assert resp.status_code == 401

    # My error handler sometimes wraps errors in "detail"; accept both formats.
    data = resp.json()
    detail = data.get("detail") or data
    assert detail["error"] in ("Unauthorized", "GitHubError")

@pytest.mark.asyncio
@respx.mock
async def test_get_issue_not_found_maps_to_404(client):
    """
    Scenario: GitHub returns 404 Not Found for a non-existent issue.
    Expectation: My /issues/{id} GET maps that into a clean 404 NotFound response.
    """
    # Mock GitHub’s GET /issues/{id} endpoint to return 404.
    route = respx.get(f"{BASE}/repos/{OWNER}/{REPO}/issues/999999").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )

    # Call my gateway endpoint with a bogus issue number.
    resp = await client.get("/issues/999999")

    # Ensure my gateway forwarded the error correctly.
    assert route.called
    assert resp.status_code == 404