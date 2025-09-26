### Coded by - Jaya Vyas - SJSUID- 019144463 #####
import os
import pytest

skip = pytest.mark.skipif(os.getenv("RUN_INTEGRATION") != "1", reason="Set RUN_INTEGRATION=1 to run")

@skip
@pytest.mark.asyncio
async def test_full_issue_lifecycle(client):
    # 1) Create
    r = await client.post("/issues", json={"title": "IT: created by tests", "body": "hello"})
    assert r.status_code == 201, r.text
    issue = r.json()
    num = issue["number"]

    # 2) Get
    r = await client.get(f"/issues/{num}")
    assert r.status_code == 200
    assert r.json()["title"] == "IT: created by tests"

    # 3) Update title
    r = await client.patch(f"/issues/{num}", json={"title": "IT: updated title"})
    assert r.status_code == 200
    assert r.json()["title"] == "IT: updated title"

    # 4) Close and reopen
    r = await client.patch(f"/issues/{num}", json={"state": "closed"})
    assert r.status_code == 200
    assert r.json()["state"] == "closed"

    r = await client.patch(f"/issues/{num}", json={"state": "open"})
    assert r.status_code == 200
    assert r.json()["state"] == "open"

    # 5) Comment
    r = await client.post(f"/issues/{num}/comments", json={"body": "IT: comment from tests"})
    assert r.status_code == 201
    comment = r.json()
    assert "id" in comment and comment["body"].startswith("IT:")

@skip
@pytest.mark.asyncio
async def test_webhook_local_signature(client):
    # This "integration" verifies the real secret + handler, without GitHub/ngrok.
    import json, os, hmac, hashlib
    secret = os.environ["WEBHOOK_SECRET"]
    body = json.dumps({"zen": "keep it logically awesome"}).encode()
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    r = await client.post(
        "/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "it-local-1",
            "X-Hub-Signature-256": sig,
        },
    )
    assert r.status_code == 204
