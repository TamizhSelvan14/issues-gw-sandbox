import os
import respx
import httpx
import pytest

OWNER = os.getenv("GITHUB_OWNER", "owner")
REPO  = os.getenv("GITHUB_REPO", "repo")
BASE  = "https://api.github.com"

@pytest.mark.asyncio
@respx.mock
async def test_list_issues_forwards_pagination_headers(client):
    link = '<https://api.github.com/...&page=2>; rel="next", <...&page=5>; rel="last"'
    headers = {
        "Link": link,
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Reset": "1700000000",
    }
    # GitHub returns issues and PRs; we include one PR to ensure our filter drops it
    payload = [
        {"number": 1, "html_url": "x", "state": "open", "title": "t", "body": None, "labels": [], "created_at": "a", "updated_at": "a"},
        {"number": 2, "html_url": "x", "state": "open", "title": "t2", "body": None, "labels": [], "created_at": "a", "updated_at": "a", "pull_request": {}},
    ]
    respx.get(f"{BASE}/repos/{OWNER}/{REPO}/issues").mock(
        return_value=httpx.Response(200, json=payload, headers=headers)
    )

    resp = await client.get("/issues?per_page=2&page=1")
    assert resp.status_code == 200
    assert resp.headers.get("Link") == link
    assert resp.headers.get("X-RateLimit-Limit") == "5000"
    # List should have filtered out the PR (length 1)
    assert len(resp.json()) == 1
