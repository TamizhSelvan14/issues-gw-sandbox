# GitHub Issues Gateway (FastAPI)

A small service that wraps the GitHub Issues REST API for a single repo, validates webhooks, ships an OpenAPI contract, and includes automated tests + Docker packaging.

---

## Features
- **Issue CRUD** (close instead of delete) and comments
- **Webhook receiver** with HMAC SHA-256 verification (`issues`, `issue_comment`, `ping`)
- **SQLite event store** with idempotent dedupe
- **OpenAPI 3.0.3 contract** available at `/public/openapi.yaml`
- **Automated tests**: unit + integration
- **Dockerized**; health check; env-based config

---

## Requirements
- Python **3.11+** (or Docker)
- GitHub **Fine-grained PAT** scoped to your test repo with:
  - **Issues: Read and write**
  - **Metadata: Read-only**
- Tunnel (e.g. **ngrok** or **Cloudflared**) for GitHub → your local machine webhooks

---

## Environment Variables
Create a `.env` file in the project root:

```env
GITHUB_TOKEN= # PAT for your test repo (fine-grained)
GITHUB_OWNER=your-username
GITHUB_REPO=your-repo
WEBHOOK_SECRET=your-webhook-secret
PORT=8080
```

---

## Run locally (no Docker)

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8080
```

- Health check: [http://localhost:8080/healthz](http://localhost:8080/healthz)  
- OpenAPI spec: [http://localhost:8080/public/openapi.yaml](http://localhost:8080/public/openapi.yaml)

---

## Run with Docker

Build the image:

```bash
docker build -t issues-gw:latest .
```

Run it (using `.env` for config):

```bash
docker run --rm -p 8080:8080 --env-file .env issues-gw:latest
```

---

## API Examples

### Create an issue
```bash
curl -X POST http://localhost:8080/issues   -H "Content-Type: application/json"   -d '{"title":"Bug: Save button broken","body":"Steps..."}' -i
```

### List issues
```bash
curl "http://localhost:8080/issues?state=open&per_page=10"
```

### Get one
```bash
curl http://localhost:8080/issues/42
```

### Update / close / reopen
```bash
curl -X PATCH http://localhost:8080/issues/42   -H "Content-Type: application/json"   -d '{"state":"closed"}'

curl -X PATCH http://localhost:8080/issues/42   -H "Content-Type: application/json"   -d '{"state":"open"}'
```

### Add a comment
```bash
curl -X POST http://localhost:8080/issues/42/comments   -H "Content-Type: application/json"   -d '{"body":"Hello from gateway!"}'
```

---

## Webhook Setup

1. Start the app (local or Docker).
2. Start tunnel:
   ```bash
   ngrok http 8080
   # or
   cloudflared tunnel --url http://localhost:8080
   ```
3. In your GitHub repo → **Settings → Webhooks → Add webhook**
   - **Payload URL:** `https://<your-tunnel>/webhook`
   - **Content type:** `application/json`
   - **Secret:** same as `WEBHOOK_SECRET`
   - **Events:** **Issues** and **Issue comments**
   - **SSL verification:** Enabled
4. Save. GitHub sends a `ping` → check:
   - Response 204 in GitHub UI
   - [http://localhost:8080/events](http://localhost:8080/events) → should show the event

---

## Tests

### Unit tests
```bash
pytest -q
```

### Integration tests (real GitHub)
```bash
# PowerShell
$env:RUN_INTEGRATION="1"; $env:PYTHONPATH="$PWD"; pytest -q tests/test_integration_github.py

# Linux/macOS
RUN_INTEGRATION=1 PYTHONPATH=$PWD pytest -q tests/test_integration_github.py
```

---

## Design Notes

- **Error mapping:** Upstream 401/403/404 → mapped to 401/404/502 with details.  
- **Pagination:** Forwards GitHub `Link` + rate limit headers; filters out PRs from `/issues`.  
- **Webhook dedupe:** Primary key `(delivery_id, action)` avoids duplicates on retries.  
- **Security:** HMAC verification (constant-time compare), env-based secrets, no secret logs.  
- **Observability:** Structured logs with `X-Request-Id`; `/healthz` endpoint for probes.  

---

