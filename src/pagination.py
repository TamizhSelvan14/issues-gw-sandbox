# src/pagination.py
from typing import Any, Dict

def _get_ci(headers: Any, name: str) -> str | None:
    """
    Case-insensitive header lookup that works for both dict and httpx.Headers.
    """
    for cand in (name, name.lower(), name.upper(), name.title()):
        try:
            val = headers.get(cand)
        except Exception:
            val = None
        if val is not None:
            return val
    return None

def forward_pagination_headers(in_headers: Any) -> Dict[str, str]:
    """
    Copy useful pagination/rate headers from GitHub to our response.
    (Case-insensitive; tolerant to httpx.Headers vs dict.)
    """
    out: Dict[str, str] = {}
    link = _get_ci(in_headers, "Link")
    if link:
        out["Link"] = link
    for k in ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]:
        v = _get_ci(in_headers, k)
        if v is not None:
            out[k] = v
    return out
