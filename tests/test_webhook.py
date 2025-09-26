### Coded by - Soham Jain - SJSUID- 019139796 ###
import hmac, hashlib, json
import pytest

def sign(secret: str, payload: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

@pytest.mark.asyncio
async def test_webhook_valid_signature(client, webhook_secret):
    body = json.dumps({"zen": "ok"}).encode()
    headers = {
        "X-GitHub-Event": "ping",
        "X-GitHub-Delivery": "local-1",
        "X-Hub-Signature-256": sign(webhook_secret, body),
        "Content-Type": "application/json",
    }
    resp = await client.post("/webhook", content=body, headers=headers)
    assert resp.status_code == 204

@pytest.mark.asyncio
async def test_webhook_invalid_signature(client):
    body = b'{"zen":"tampered"}'
    headers = {
        "X-GitHub-Event": "ping",
        "X-GitHub-Delivery": "local-2",
        "X-Hub-Signature-256": "sha256=" + "00"*32,  # wrong sig
        "Content-Type": "application/json",
    }
    resp = await client.post("/webhook", content=body, headers=headers)
    assert resp.status_code == 401
