### Prachi Gupta SJSU ID- 019106594 ###

# src/main.py
import uuid
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from .config import get_settings
from .routes import issues, webhook
from .storage import init_db
from fastapi.staticfiles import StaticFiles


from pathlib import Path

settings = get_settings()

# Simple structured logger
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(20))  # INFO
log = structlog.get_logger()
BASE_DIR = Path(__file__).resolve().parent.parent  # project root
SPEC_DIR = BASE_DIR / "public"

app = FastAPI(title="GitHub Issues Gateway", version="0.1.0")

# serve /public/* from the public directory regardless of where you run uvicorn
app.mount("/public", StaticFiles(directory=str(SPEC_DIR)), name="public")

# Request ID middleware (adds X-Request-Id)
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = str(uuid.uuid4())
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["X-Request-Id"] = rid
    return response

# Clean 400 for Pydantic validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": "BadRequest", "message": "Invalid request payload", "details": exc.errors()},
    )

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

# Include our routers
app.include_router(issues.router)
app.include_router(webhook.router)

# Init the SQLite DB on startup
@app.on_event("startup")
async def _startup():
    await init_db()
    log.info("startup_complete")
