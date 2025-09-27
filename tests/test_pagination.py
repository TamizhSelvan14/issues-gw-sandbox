### Coded by - Soham Jain - SJSUID- 019139796 ###
import os
import respx
import httpx
import pytest

# Read GitHub repository details from environment variables (with defaults)
OWNER = os.getenv("GITHUB_OWNER", "owner")
REPO  = os.getenv("GITHUB_REPO", "repo")
BASE  = "https://api.github.com"

@pytest.mark.asyncio
@respx.mock
async def test_list_issues_forwards_pagination_headers(client):
    """
    Test that our /issues endpoint:
    - Forwards pagination and rate-limit headers from GitHub
    - Filters out pull requests from the issue list
    """

    # Example GitHub-style pagination link header
    link = '<https://api.github.com/...&page=2>; rel="next", <...&page=5>; rel="last"'
    
    # Mock headers returned by GitHub API
    headers = {
        "Link": link,
        "X-RateLimit-Limit": "5000",
        "X-RateLimit-Remaining": "4999",
        "X-RateLimit-Reset": "1700000000",
    }

    # Mock GitHub API payload: includes one issue and one pull request (PR)
    # Pull requests show up in the issues API but should be excluded from results
    payload = [
        # A normal issue
        {"number": 1, "html_url": "x", "state": "open", "title": "t", "body": None, 
         "labels": [], "created_at": "a", "updated_at": "a"},
        # A PR disguised as an issue (identified by "pull_request" key)
        {"number": 2, "html_url": "x", "state": "open", "title": "t2", "body": None, 
         "labels": [], "created_at": "a", "updated_at": "a", "pull_request": {}},
    ]

    # Mock the GitHub /issues endpoint response with respx
    respx.get(f"{BASE}/repos/{OWNER}/{REPO}/issues").mock(
        return_value=httpx.Response(200, json=payload, headers=headers)
    )

    # Call our FastAPI client endpoint
    resp = await client.get("/issues?per_page=2&page=1")

    # Validate response status
    assert resp.status_code == 200
    
    # Check that pagination headers are forwarded correctly
    assert resp.headers.get("Link") == link
    assert resp.headers.get("X-RateLimit-Limit") == "5000"

    # Ensure the PR was filtered out -> only 1 issue should remain
    assert len(resp.json()) == 1
