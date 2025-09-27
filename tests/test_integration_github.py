### Coded by - Jaya Vyas - SJSUID- 019144463 #####
# File: tests/test_integration.py
# Purpose: True integration tests that hit the live GitHub API through my gateway.
# Notes: These only run when RUN_INTEGRATION=1 is set. Otherwise they are skipped
# to avoid consuming GitHub rate limits or creating noise issues in CI.

import os
import pytest

# I gate these tests behind an env flag because they require a valid PAT + repo.
skip = pytest.mark.skipif(os.getenv("RUN_INTEGRATION") != "1", reason="Set RUN_INTEGRATION=1 to run")

@skip
@pytest.mark.asyncio
async def test_full_issue_lifecycle(client):
    """
    End-to-end lifecycle test against GitHub Issues API through my gateway.
    I verify that create → get → update → close → reopen → comment all succeed.
    """
    # 1) Create an issue
    r = await client.post("/issues", json={"title": "IT: created by tests", "body": "hello"})
    assert r.status_code == 201, r.text
    issue = r.json()
    num = issue["number"]

    # 2) Get the issue back and validate title
    r = await client.get(f"/issues/{num}")
    assert r.status_code == 200
    assert r.json()["title"] == "IT: created by tests"

    # 3) Update the issue title
    r = await client.patch(f"/issues/{num}", json={"title": "IT: updated title"})
    assert r.status_code == 200
    assert r.json()["title"] == "IT: updated title"

    # 4) Close the issue, then reopen it
    r = await client.patch(f"/issues/{num}", json={"state": "closed"})
    assert r.status_code == 200
    assert r.json()["state"] == "closed"

    r = await client.patch(f"/issues/{num}", json={"state": "open"})
    assert r.status_code == 200
    assert r.json()["state"] == "open"

    # 5) Add a comment
    r = await client.post(f"/issues/{num}/comments", json={"body": "IT: comment from tests"})
    assert r.status_code == 201
    comment = r.json()
    assert "id" in comment and comment["body"].startswith("IT:")

@skip
@pytest.mark.asyncio
async def test_webhook_local_signature(client):
    """
    Integration test for webhook signature validation.
    Instead of GitHub/ngrok, I craft a signed ping event locally using
    the same HMAC SHA-256 logic as GitHub.
    """
    import json, os, hmac, hashlib

    secret = os.environ["WEBHOOK_SECRET"]
    body = json.dumps({"zen": "keep it logically awesome"}).encode()

    # Compute signature with real secret to mimic GitHub’s behavior
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    # Post webhook payload with headers
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

    # Expect gateway to validate and ack with 204 No Content
    assert r.status_code == 204