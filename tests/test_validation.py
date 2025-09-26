import pytest

@pytest.mark.asyncio
async def test_create_issue_requires_title(client):
    # Missing title field entirely
    resp = await client.post("/issues", json={})
    assert resp.status_code == 400

    # Empty title string
    resp = await client.post("/issues", json={"title": "   "})
    assert resp.status_code == 400
    body = resp.json()
    assert body.get("detail") or body.get("message")  # either our 400 or FastAPI's
