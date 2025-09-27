### Coded by - Jaya Vyas - SJSUID- 019144463 #####
# File: tests/conftest.py
# Purpose: Centralized pytest fixtures for async testing of my FastAPI app.
# Notes: I load environment variables once per test session, expose the ASGI app,
# and provide an httpx AsyncClient so tests can hit routes without running uvicorn.

import os
import asyncio
import pytest
import httpx
from dotenv import load_dotenv

# I load .env once at import time so all session-scoped fixtures see the same config.
# Expected keys: GITHUB_TOKEN, OWNER, REPO, WEBHOOK_SECRET, etc.
load_dotenv()

@pytest.fixture(scope="session")
def anyio_backend():
    """
    I tell anyio/pytest-asyncio to use 'asyncio' as the event loop backend
    for the entire test session. This keeps timing consistent across tests.
    """
    return "asyncio"

@pytest.fixture(scope="session")
def webhook_secret() -> str:
    """
    I surface the webhook secret to tests and fail fast if it's missing,
    so I don't debug flaky signature checks later.
    """
    secret = os.getenv("WEBHOOK_SECRET")
    assert secret, "WEBHOOK_SECRET missing in .env for tests"
    return secret

@pytest.fixture(scope="session")
def app():
    """
    I import the FastAPI app AFTER .env is loaded so settings are hydrated
    before app startup hooks read them.
    """
    from src.main import app as fastapi_app
    return fastapi_app

@pytest.fixture
async def client(app):
    """
    I provide an async HTTP client that talks to the ASGI app directly—
    no uvicorn process needed. This makes tests fast and deterministic.
    Usage in tests:
        async def test_healthz(client):
            resp = await client.get("/healthz")
            assert resp.status_code == 200
    """
    # base_url is required by httpx; "http://testserver" is a conventional placeholder.
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac
