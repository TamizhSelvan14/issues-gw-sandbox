# src/models.py
"""
Pydantic models for GitHub-like Issues & Comments API.

Tamizh Selvan (SJSU ID: 019148896)
- Added docstrings for clarity.
- Switched mutable default for Issue.labels to Field(default_factory=list).
- Kept error/details flexible for upstream compatibility.
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


# ======================
# Request payload models
# ======================

# Payload to create a new issue
class CreateIssue(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        description="Short summary of the issue"
    )
    body: Optional[str] = None
    labels: Optional[List[str]] = None


# Payload to update an existing issue
class UpdateIssue(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    body: Optional[str] = None
    state: Optional[Literal["open", "closed"]] = None


# Payload to create a new comment on an issue
class CreateComment(BaseModel):
    body: str = Field(..., min_length=1)


# =======================
# Response subset models
# =======================

# Subset of GitHub label fields
class Label(BaseModel):
    name: str


# Issue response (subset of fields we care about)
class Issue(BaseModel):
    number: int
    html_url: str
    state: Literal["open", "closed"]
    title: str
    body: Optional[str] = None
    labels: List[Label] = Field(default_factory=list)  # safer than using []
    created_at: str
    updated_at: str


# Comment response (subset)
class Comment(BaseModel):
    id: int
    body: str
    user: Dict[str, Any]
    created_at: str
    html_url: str


# Standardized error envelope returned by the API
class Error(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
