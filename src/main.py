### Coded by - Prachi Gupta SJSU ID- 019106594 ###

# src/main.py
import uuid
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import get_settings
from .routes import issues, webhook
from .storage import init_db

# load settings
settings = get_settings()

# configure simple logger (INFO level)
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(20))
log = structlog.get_logger()

# project directories
BASE_DIR = Path(__file__).resolve().parent.parent   # project root
SPEC_DIR = BASE_DIR / "public"

# main FastAPI app
app = FastAPI(title="GitHub Issues Gateway", version="0.1.0")

# serve static files from /public directory
app.mount("/public", StaticFiles(directory=str(SPEC_DIR)), name="public")


# middleware -> add unique request id for every request
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    rid = str(uuid.uuid4())
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["X-Request-Id"] = rid
    return response


# custom exception handler -> clean error message for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "BadRequest",
            "message": "Invalid request payload",
            "details": exc.errors(),
        },
    )


# simple health check endpoint
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


# include routes (issues + webhook)
app.include_router(issues.router)
app.include_router(webhook.router)


# run DB initialization when app starts
@app.on_event("startup")
async def _startup():
    await init_db()
    log.info("startup_complete")
