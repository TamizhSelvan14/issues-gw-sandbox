# src/routes/issues.py
from fastapi import APIRouter, HTTPException, Response, Query, Path
from typing import Optional, List
from ..models import CreateIssue, UpdateIssue, Issue, Comment, CreateComment
from .. import github_client as gh
from ..pagination import forward_pagination_headers

# router for issues related APIs
router = APIRouter()


@router.post("/issues", status_code=201, response_model=Issue)
async def create_issue(payload: CreateIssue, response: Response):
    """
    Create a new issue in GitHub repo
    -> On success returns 201 with Location header
    """
    # title check (title should not be empty)
    if not payload.title or not payload.title.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "BadRequest", "message": "title is required"}
        )
    try:
        # call github client to create issue
        created = await gh.create_issue(payload.title, payload.body, payload.labels)
        response.headers["Location"] = f"/issues/{created['number']}"
        return created
    except gh.GitHubError as e:
        # handle errors properly
        if e.status in (401, 403):
            raise HTTPException(
                status_code=401,
                detail={"error": "Unauthorized", "message": e.message, "details": e.details}
            )
        elif e.status == 404:
            raise HTTPException(
                status_code=404,
                detail={"error": "NotFound", "message": "Repo not found or no access", "details": e.details}
            )
        else:
            raise HTTPException(
                status_code=502,
                detail={"error": "GitHubError", "message": e.message, "details": e.details}
            )


@router.get("/issues", response_model=List[Issue])
async def list_issues(
    response: Response,
    state: str = Query("open", pattern="^(open|closed|all)$"),
    labels: Optional[str] = Query(None, description='Comma-separated labels like "bug,frontend"'),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
):
    """
    List issues from GitHub repo
    -> Pagination is supported (like GitHub)
    -> Also forwards pagination headers
    """
    try:
        issues, headers = await gh.list_issues(state, labels, page, per_page)
        # forward pagination headers
        for k, v in forward_pagination_headers(headers).items():
            response.headers[k] = v
        return issues
    except gh.GitHubError as e:
        code = 401 if e.status in (401, 403) else (404 if e.status == 404 else 502)
        err = "Unauthorized" if code == 401 else ("NotFound" if code == 404 else "GitHubError")
        raise HTTPException(
            status_code=code,
            detail={"error": err, "message": e.message, "details": e.details}
        )


@router.get("/issues/{number}", response_model=Issue)
async def get_issue(number: int = Path(..., ge=1)):
    """
    Get single issue by its number
    """
    try:
        return await gh.get_issue(number)
    except gh.GitHubError as e:
        if e.status == 404:
            raise HTTPException(
                status_code=404,
                detail={"error": "NotFound", "message": f"Issue {number} not found", "details": e.details}
            )
        code = 401 if e.status in (401, 403) else 502
        err = "Unauthorized" if code == 401 else "GitHubError"
        raise HTTPException(
            status_code=code,
            detail={"error": err, "message": e.message, "details": e.details}
        )


@router.patch("/issues/{number}", response_model=Issue)
async def patch_issue(
    number: int = Path(..., ge=1),
    payload: UpdateIssue = ...,
):
    """
    Update issue by number
    -> can update title, body or state (open/closed)
    """
    try:
        return await gh.update_issue(number, payload.title, payload.body, payload.state)
    except gh.GitHubError as e:
        if e.status == 404:
            raise HTTPException(
                status_code=404,
                detail={"error": "NotFound", "message": f"Issue {number} not found", "details": e.details}
            )
        code = 401 if e.status in (401, 403) else 502
        err = "Unauthorized" if code == 401 else "GitHubError"
        raise HTTPException(
            status_code=code,
            detail={"error": err, "message": e.message, "details": e.details}
        )


@router.post("/issues/{number}/comments", status_code=201, response_model=Comment)
async def add_comment(number: int, payload: CreateComment):
    """
    Add comment to issue by number
    """
    # comment body should not be empty
    if not payload.body or not payload.body.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "BadRequest", "message": "comment body is required"}
        )
    try:
        return await gh.create_comment(number, payload.body)
    except gh.GitHubError as e:
        if e.status == 404:
            raise HTTPException(
                status_code=404,
                detail={"error": "NotFound", "message": f"Issue {number} not found", "details": e.details}
            )
        code = 401 if e.status in (401, 403) else 502
        err = "Unauthorized" if code == 401 else "GitHubError"
        raise HTTPException(
            status_code=code,
            detail={"error": err, "message": e.message, "details": e.details}
        )
