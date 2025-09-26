### Coded by - Jaya Vyas - SJSUID- 019144463 #####
# tests/conftest.py
import os
import asyncio
import pytest
import httpx
from dotenv import load_dotenv

# Load .env once for tests (GITHUB_TOKEN, OWNER, REPO, WEBHOOK_SECRET, etc.)
load_dotenv()

@pytest.fixture(scope="session")
def anyio_backend():
    # Let pytest-asyncio/anyio pick asyncio by default
    return "asyncio"

@pytest.fixture(scope="session")
def webhook_secret() -> str:
    secret = os.getenv("WEBHOOK_SECRET")
    assert secret, "WEBHOOK_SECRET missing in .env for tests"
    return secret

@pytest.fixture(scope="session")
def app():
    # Import AFTER .env is loaded so settings read correctly
    from src.main import app as fastapi_app
    return fastapi_app

@pytest.fixture
async def client(app):
    # Async test client that exercises the ASGI app directly (no uvicorn needed)
    async with httpx.AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac
