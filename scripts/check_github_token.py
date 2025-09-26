### Coded by - Soham Jain - SJSUID- 019139796 ###

# scripts/check_github_token.py
import os, sys
import httpx
from dotenv import load_dotenv

load_dotenv()  # reads .env in your project root

token = os.getenv("GITHUB_TOKEN")
owner = os.getenv("GITHUB_OWNER")
repo = os.getenv("GITHUB_REPO")

def fail(msg: str, code: int = 1):
    print(f"[ERROR] {msg}")
    sys.exit(code)

if not token:
    fail("GITHUB_TOKEN is missing in .env")
if not owner:
    fail("GITHUB_OWNER is missing in .env")
if not repo:
    fail("GITHUB_REPO is missing in .env")

url = f"https://api.github.com/repos/{owner}/{repo}/issues"
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "issues-gw/check",
}
params = {"state": "open", "per_page": 1}

print(f"[INFO] Checking GitHub Issues API for {owner}/{repo} ...")
with httpx.Client(timeout=20) as client:
    r = client.get(url, headers=headers, params=params)
    print(f"[INFO] Status: {r.status_code}")
    # Show rate limit info if available
    for k in ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]:
        if k in r.headers:
            print(f"[INFO] {k}: {r.headers[k]}")

    if r.status_code == 200:
        print("[SUCCESS] Token works! Issues endpoint is accessible.")
        if isinstance(r.json(), list):
            print(f"[INFO] Returned {len(r.json())} issue(s) (showing up to 1).")
        sys.exit(0)

    # Helpful diagnostics
    try:
        body = r.json()
    except Exception:
        body = {"raw": r.text[:200]}

    if r.status_code in (401, 403):
        print("[ERROR] Unauthorized/Forbidden. Common causes:")
        print("  - Token is wrong or expired")
        print("  - Token lacks 'Issues: Read and write' for THIS repo")
        print("  - Repo not selected when creating the fine-grained token")
    elif r.status_code == 404:
        print("[ERROR] Not found. Common causes:")
        print("  - GITHUB_OWNER or GITHUB_REPO is misspelled")
        print("  - The token does not have access to this private repo")
    else:
        print("[ERROR] Unexpected status. Response body shown below.")

    print("[DEBUG] Response JSON (truncated):", str(body)[:500])
    sys.exit(2)
