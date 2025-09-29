# src/pagination.py
# Tamizh Selvan (SJSU ID: 019148896)
# TS: Utilities for forwarding pagination and rate-limit headers.

from typing import Any, Dict


#  Case-insensitive header lookup that works for both dict and httpx.Headers.
def _get_ci(headers: Any, name: str) -> str | None:
    for cand in (name, name.lower(), name.upper(), name.title()):
        try:
            val = headers.get(cand)
        except Exception:
            val = None
        if val is not None:
            return val
    return None


#  Forward only relevant pagination and rate-limit headers from upstream (GitHub) to our response.
def forward_pagination_headers(in_headers: Any) -> Dict[str, str]:
    out: Dict[str, str] = {}
    link = _get_ci(in_headers, "Link")
    if link:
        out["Link"] = link
    for k in ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]:
        v = _get_ci(in_headers, k)
        if v is not None:
            out[k] = v
    return out
