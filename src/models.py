### Tamizh Selvan SJSUID- 019148896 ###
# src/models.py
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# Requests
class CreateIssue(BaseModel):
    title: str = Field(..., min_length=1, description="Short summary of the issue")
    body: Optional[str] = None
    labels: Optional[List[str]] = None

class UpdateIssue(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    body: Optional[str] = None
    state: Optional[Literal["open", "closed"]] = None

class CreateComment(BaseModel):
    body: str = Field(..., min_length=1)

# Responses (subset of GitHub fields)
class Label(BaseModel):
    name: str

class Issue(BaseModel):
    number: int
    html_url: str
    state: Literal["open", "closed"]
    title: str
    body: Optional[str] = None
    labels: List[Label] = []
    created_at: str
    updated_at: str

class Comment(BaseModel):
    id: int
    body: str
    user: dict
    created_at: str
    html_url: str

class Error(BaseModel):
    error: str
    message: str
    details: dict | None = None
