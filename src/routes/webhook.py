import json
import hmac
import hashlib
import structlog
from fastapi import APIRouter, Header, HTTPException, Request, Response, Query
from ..config import get_settings
from ..storage import insert_event, list_recent_events

router = APIRouter()
log = structlog.get_logger()
settings = get_settings()

def verify_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """
    Verify GitHub's HMAC SHA-256 signature: header format 'sha256=<hexdigest>'.
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    sent_hex = signature_header.split("=", 1)[1]
    calc_hex = hmac.new(settings.WEBHOOK_SECRET.encode(), msg=raw_body, digestmod=hashlib.sha256).hexdigest()
    # Constant-time comparison prevents timing attacks
    return hmac.compare_digest(sent_hex, calc_hex)

@router.post("/webhook", status_code=204)
async def webhook(
    request: Request,
    x_github_event: str = Header(..., alias="X-GitHub-Event"),
    x_github_delivery: str = Header(..., alias="X-GitHub-Delivery"),
    x_hub_signature_256: str | None = Header(None, alias="X-Hub-Signature-256"),
):
    # 1) Read raw body first (for HMAC)
    raw = await request.body()

    # 2) Verify signature
    if not verify_signature(raw, x_hub_signature_256):
        raise HTTPException(status_code=401, detail={"error": "InvalidSignature", "message": "HMAC verification failed"})

    # 3) Parse payload (keep handler fast!)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        payload = {}

    # 4) Accept only issues, issue_comment, or ping
    if x_github_event not in ("issues", "issue_comment", "ping"):
        raise HTTPException(status_code=400, detail={"error": "UnsupportedEvent", "message": f"Event '{x_github_event}' not supported"})

    action = payload.get("action")
    issue_number = (payload.get("issue") or {}).get("number")

    # 5) Persist a compact record (idempotent via PK)
    await insert_event(x_github_delivery, x_github_event, action, issue_number, json.dumps(payload))

    # 6) Quick ACK
    log.info("webhook_ack", delivery_id=x_github_delivery, gh_event=x_github_event, action=action, issue_number=issue_number)

    return Response(status_code=204)

@router.get("/events")
async def get_events(limit: int = Query(20, ge=1, le=100)):
    rows = await list_recent_events(limit)
    return [
        {"id": r[0], "event": r[1], "action": r[2], "issue_number": r[3], "timestamp": r[4]}
        for r in rows
    ]
