from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db.models import Branch, Message, ShareToken, Thread, User
from ..db.session import get_db
from ..deps import get_current_user

router = APIRouter(tags=["share"])


class ShareBody(BaseModel):
    thread_id: str = Field(..., min_length=32, max_length=64)
    branch_id: str | None = None
    expires_at: str | None = None


@router.post("/share", status_code=201)
def create_share(
    body: ShareBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = db.query(Thread).filter(Thread.id == body.thread_id, Thread.user_id == user.id).first()
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Thread not found")
    token = secrets.token_urlsafe(24)
    exp = None
    if body.expires_at:
        try:
            exp = datetime.fromisoformat(body.expires_at.replace("Z", "+00:00"))
        except Exception:
            exp = None
    st = ShareToken(
        token=token,
        thread_id=t.id,
        branch_id=body.branch_id or t.active_branch_id,
        expires_at=exp,
    )
    db.add(st)
    db.commit()
    return {
        "token": token,
        "url": f"/share/{token}",
        "path": f"/share/{token}",
    }


@router.get("/share/{token}")
def read_share(token: str, db: Session = Depends(get_db)):
    st = db.query(ShareToken).filter(ShareToken.token == token).first()
    if not st:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    if st.expires_at and st.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_410_GONE, "Link expired")
    t = db.query(Thread).filter(Thread.id == st.thread_id).first()
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Thread gone")
    msgs = (
        db.query(Message)
        .filter(Message.thread_id == t.id, Message.branch_id == st.branch_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    br_row = (
        db.query(Branch)
        .filter(Branch.id == st.branch_id, Branch.thread_id == t.id)
        .first()
    )
    planning_transcript: list | None = None
    if br_row and isinstance(br_row.extra, dict):
        pt = br_row.extra.get("planning_ui_events")
        if isinstance(pt, list):
            planning_transcript = pt
    return {
        "thread": {
            "id": t.id,
            "title": t.title,
            "phase": t.phase,
            "updated_at": t.updated_at.isoformat(),
            "archived": False,
            "pinned": False,
        },
        "messages": [
            {
                "id": m.id,
                "branch_id": m.branch_id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
                "metadata": m.extra or {},
                "agent": m.agent,
            }
            for m in msgs
        ],
        "planning_transcript": planning_transcript or [],
    }
