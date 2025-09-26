# src/github_client.py
import httpx
from typing import Any, Dict, List, Optional, Tuple
from .config import get_settings

settings = get_settings()

BASE = "https://api.github.com"
OWNER = settings.GITHUB_OWNER
REPO = settings.GITHUB_REPO

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
    "User-Agent": "issues-gw/1.0",
}

class GitHubError(Exception):
    """Custom error so we can map GitHub problems to our API responses."""
    def __init__(self, status: int, message: str, details: Dict[str, Any] | None = None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.details = details or {}

def _normalize_issue(gh_issue: Dict[str, Any]) -> Dict[str, Any]:
    labels = [{"name": l["name"]} for l in gh_issue.get("labels", []) if isinstance(l, dict) and "name" in l]
    return {
        "number": gh_issue["number"],
        "html_url": gh_issue["html_url"],
        "state": gh_issue["state"],
        "title": gh_issue["title"],
        "body": gh_issue.get("body"),
        "labels": labels,
        "created_at": gh_issue["created_at"],
        "updated_at": gh_issue["updated_at"],
    }

async def _raise_if_error(resp: httpx.Response):
    if resp.is_error:
        try:
            data = resp.json()
            msg = data.get("message", resp.text or "GitHub error")
        except Exception:
            msg = resp.text or "GitHub error"
            data = None
        raise GitHubError(resp.status_code, msg, {"github_status": resp.status_code, "github_message": msg})

async def create_issue(title: str, body: Optional[str], labels: Optional[List[str]]) -> Dict[str, Any]:
    payload = {"title": title}
    if body is not None:
        payload["body"] = body
    if labels:
        payload["labels"] = labels
    async with httpx.AsyncClient(base_url=BASE, headers=HEADERS, timeout=20) as client:
        resp = await client.post(f"/repos/{OWNER}/{REPO}/issues", json=payload)
        await _raise_if_error(resp)
        return _normalize_issue(resp.json())

async def list_issues(state: str, labels: Optional[str], page: int, per_page: int) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    params = {"state": state, "page": page, "per_page": per_page}
    if labels:
        params["labels"] = labels
    async with httpx.AsyncClient(base_url=BASE, headers=HEADERS, timeout=20) as client:
        resp = await client.get(f"/repos/{OWNER}/{REPO}/issues", params=params)
        await _raise_if_error(resp)
        # Filter out PRs (GitHub mixes PRs in the issues list; PR items have "pull_request" key)
        issues = [_normalize_issue(x) for x in resp.json() if "pull_request" not in x]
        return issues, dict(resp.headers)


async def get_issue(number: int) -> Dict[str, Any]:
    async with httpx.AsyncClient(base_url=BASE, headers=HEADERS, timeout=20) as client:
        resp = await client.get(f"/repos/{OWNER}/{REPO}/issues/{number}")
        await _raise_if_error(resp)
        return _normalize_issue(resp.json())

async def update_issue(number: int, title: Optional[str], body: Optional[str], state: Optional[str]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    if title is not None:
        payload["title"] = title
    if body is not None:
        payload["body"] = body
    if state is not None:
        payload["state"] = state  # "open" or "closed"
    async with httpx.AsyncClient(base_url=BASE, headers=HEADERS, timeout=20) as client:
        resp = await client.patch(f"/repos/{OWNER}/{REPO}/issues/{number}", json=payload)
        await _raise_if_error(resp)
        return _normalize_issue(resp.json())
    
async def create_comment(number: int, body: str) -> Dict[str, Any]:
    payload = {"body": body}
    async with httpx.AsyncClient(base_url=BASE, headers=HEADERS, timeout=20) as client:
        resp = await client.post(f"/repos/{OWNER}/{REPO}/issues/{number}/comments", json=payload)
        await _raise_if_error(resp)
        return resp.json()

