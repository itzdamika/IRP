from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from ..db.models import ArtifactRecord, Thread, User
from ..db.session import get_db
from ..deps import bearer, get_current_user, user_from_token

router = APIRouter(tags=["artifacts"])


@router.get("/artifacts/{artifact_id}/download")
def download_artifact(
    artifact_id: str,
    token: str | None = Query(
        None,
        description="Optional JWT for embedding PDF in iframes (use instead of Authorization).",
    ),
    db: Session = Depends(get_db),
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    user: User | None = None
    if cred and cred.scheme.lower() == "bearer":
        try:
            user = get_current_user(db, cred)
        except HTTPException:
            user = None
    if user is None and token:
        user = user_from_token(db, token)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    r = db.query(ArtifactRecord).filter(ArtifactRecord.id == artifact_id).first()
    if not r:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Artifact not found")
    t = db.query(Thread).filter(Thread.id == r.thread_id).first()
    if not t or t.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your file")
    p = Path(r.path)
    if not p.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "File missing on disk")
    return FileResponse(
        str(p),
        filename=r.filename,
        media_type=r.mime_type,
        content_disposition_type="inline",
    )
