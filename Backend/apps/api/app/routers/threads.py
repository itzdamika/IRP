from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db.models import ArtifactRecord, Branch, Message, Thread, User
from ..db.session import get_db
from ..deps import get_current_user
from ..services import governance_bridge as gb
from ..services import jobs as job_svc
from ..services.thread_title import suggest_title_for_thread

router = APIRouter(prefix="/threads", tags=["threads"])


class ThreadCreate(BaseModel):
    title: str | None = Field(None, max_length=512)


class ThreadPatch(BaseModel):
    title: str | None = Field(None, max_length=512)
    archived: bool | None = None
    pinned: bool | None = None
    active_branch_id: str | None = None


class PostMessageBody(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000)
    branch_id: str | None = None
    client_message_id: str | None = None
    background: bool = Field(
        default=False,
        description="If true, return 202 and run the turn in a background worker (poll job URL).",
    )


class DevMessageBody(BaseModel):
    content: str = Field(..., min_length=1, max_length=50000)
    branch_id: str | None = None


class RegenerateBody(BaseModel):
    branch_id: str | None = None


class EditMessageBody(BaseModel):
    new_content: str = Field(..., min_length=1, max_length=50000)
    branch_id: str | None = None


def _thread(db: Session, user: User, thread_id: str) -> Thread:
    t = db.query(Thread).filter(Thread.id == thread_id, Thread.user_id == user.id).first()
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Thread not found")
    return t


def _settings_row(db: Session, user: User):
    from ..db.models import UserSettingsRow

    return db.query(UserSettingsRow).filter(UserSettingsRow.user_id == user.id).first()


def _branch_id(t: Thread, body_branch: str | None) -> str:
    return body_branch or t.active_branch_id


@router.get("")
def list_threads(
    limit: int = 30,
    archived: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Thread).filter(Thread.user_id == user.id, Thread.archived == archived)
    rows = q.order_by(Thread.updated_at.desc()).limit(min(limit, 100)).all()
    return {
        "items": [
            {
                "id": t.id,
                "title": t.title,
                "phase": t.phase,
                "updated_at": t.updated_at.isoformat(),
                "archived": t.archived,
                "pinned": t.pinned,
            }
            for t in rows
        ],
        "next_cursor": None,
    }


@router.post("", status_code=201)
def create_thread(
    body: ThreadCreate | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = Thread(user_id=user.id, title=(body.title if body and body.title else "New chat"))
    db.add(t)
    db.flush()
    t.active_branch_id = t.id
    db.add(
        Branch(
            id=t.active_branch_id,
            thread_id=t.id,
            label="main",
            parent_branch_id=None,
            engine_state_blob=None,
        )
    )
    db.commit()
    db.refresh(t)
    return {
        "id": t.id,
        "title": t.title,
        "phase": t.phase,
        "active_branch_id": t.active_branch_id,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
        "archived": t.archived,
        "pinned": t.pinned,
    }


@router.get("/{thread_id}")
def get_thread(
    thread_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = _thread(db, user, thread_id)
    return {
        "id": t.id,
        "title": t.title,
        "phase": t.phase,
        "active_branch_id": t.active_branch_id,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
        "archived": t.archived,
        "pinned": t.pinned,
    }


@router.post("/{thread_id}/auto-title")
def auto_title_thread(
    thread_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """After enough messages, suggest a short topic title (replaces long first-message titles too)."""
    t = _thread(db, user, thread_id)
    n = (
        db.query(Message)
        .filter(
            Message.thread_id == t.id,
            Message.branch_id == t.active_branch_id,
        )
        .count()
    )
    if n < 6:
        return {"title": t.title, "updated": False, "reason": "not_enough_messages"}
    new_title = suggest_title_for_thread(db, t)
    if not new_title or new_title.strip() == (t.title or "").strip():
        return {"title": t.title, "updated": False}
    t.title = new_title[:512]
    t.updated_at = datetime.now(timezone.utc)
    db.add(t)
    db.commit()
    db.refresh(t)
    return {"title": t.title, "updated": True}


@router.patch("/{thread_id}")
def patch_thread(
    thread_id: str,
    body: ThreadPatch,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = _thread(db, user, thread_id)
    if body.title is not None:
        t.title = body.title
    if body.archived is not None:
        t.archived = body.archived
    if body.pinned is not None:
        t.pinned = body.pinned
    if body.active_branch_id is not None:
        br = (
            db.query(Branch)
            .filter(
                Branch.id == body.active_branch_id,
                Branch.thread_id == t.id,
            )
            .first()
        )
        if not br:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid branch")
        t.active_branch_id = body.active_branch_id
    t.updated_at = datetime.now(timezone.utc)
    db.add(t)
    db.commit()
    db.refresh(t)
    return {
        "id": t.id,
        "title": t.title,
        "phase": t.phase,
        "active_branch_id": t.active_branch_id,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
        "archived": t.archived,
        "pinned": t.pinned,
    }


@router.delete("/{thread_id}", status_code=204)
def delete_thread(
    thread_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = _thread(db, user, thread_id)
    gb.drop_engine_cache(thread_id)
    db.delete(t)
    db.commit()
    return Response(status_code=204)


@router.get("/{thread_id}/branches")
def list_branches(
    thread_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = _thread(db, user, thread_id)
    rows = db.query(Branch).filter(Branch.thread_id == t.id).order_by(Branch.created_at.asc()).all()
    out = []
    for b in rows:
        cnt = (
            db.query(Message)
            .filter(Message.thread_id == t.id, Message.branch_id == b.id)
            .count()
        )
        out.append(
            {
                "id": b.id,
                "parent_message_id": b.forked_from_message_id,
                "label": b.label,
                "created_at": b.created_at.isoformat(),
                "message_count": cnt,
            }
        )
    return {"items": out}


@router.get("/{thread_id}/messages/{message_id}/fork-versions")
def message_fork_versions(
    thread_id: str,
    message_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Branches created by editing this user message (ChatGPT-style 1/N switcher)."""
    t = _thread(db, user, thread_id)
    forks = (
        db.query(Branch)
        .filter(
            Branch.thread_id == t.id,
            Branch.forked_from_message_id == message_id,
        )
        .order_by(Branch.created_at.asc())
        .all()
    )
    if not forks:
        return {
            "has_fork_versions": False,
            "branch_ids": [],
            "current_index": 0,
            "total": 0,
        }
    parent_id = forks[0].parent_branch_id
    if not parent_id:
        return {
            "has_fork_versions": False,
            "branch_ids": [],
            "current_index": 0,
            "total": 0,
        }
    branch_ids = [parent_id] + [f.id for f in forks]
    current = t.active_branch_id
    try:
        idx = branch_ids.index(current)
    except ValueError:
        return {
            "has_fork_versions": True,
            "branch_ids": branch_ids,
            "current_index": 0,
            "total": len(branch_ids),
            "active_in_family": False,
        }
    return {
        "has_fork_versions": True,
        "branch_ids": branch_ids,
        "current_index": idx,
        "total": len(branch_ids),
        "active_in_family": True,
    }


@router.get("/{thread_id}/messages")
def get_messages(
    thread_id: str,
    branch_id: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = _thread(db, user, thread_id)
    bid = branch_id or t.active_branch_id
    lim = min(max(limit, 1), 2000)
    msgs = (
        db.query(Message)
        .filter(Message.thread_id == t.id, Message.branch_id == bid)
        .order_by(Message.created_at.desc())
        .limit(lim)
        .all()
    )
    msgs = list(reversed(msgs))
    br_row = (
        db.query(Branch)
        .filter(Branch.id == bid, Branch.thread_id == t.id)
        .first()
    )
    planning_transcript: list | None = None
    if br_row and isinstance(br_row.extra, dict):
        raw_pt = br_row.extra.get("planning_ui_events")
        if isinstance(raw_pt, list):
            planning_transcript = raw_pt
    return {
        "branch_id": bid,
        "items": [
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
        "next_cursor": None,
    }


@router.post("/{thread_id}/messages")
def post_message(
    thread_id: str,
    body: PostMessageBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = _thread(db, user, thread_id)
    srow = _settings_row(db, user)
    bid = _branch_id(t, body.branch_id)
    eng = gb.get_engine(db, t, bid, srow)
    if eng.state.internal_busy:
        raise HTTPException(status.HTTP_409_CONFLICT, "Session is busy (planning in progress)")
    if body.background:
        job_id = job_svc.submit_message_turn(t.id, user.id, body.content, body.branch_id)
        return Response(
            status_code=202,
            headers={"Location": f"/v1/threads/{t.id}/planning/jobs/{job_id}"},
            content=json.dumps(
                {
                    "job_id": job_id,
                    "status_url": f"/v1/threads/{t.id}/planning/jobs/{job_id}",
                    "ws_url": f"/v1/ws/jobs/{job_id}",
                    "poll_after_ms": 600,
                }
            ),
            media_type="application/json",
        )
    if t.title == "New chat" and body.content.strip():
        s0 = body.content.strip()
        t.title = s0[:100] + ("…" if len(s0) > 100 else "")
        db.add(t)
        db.commit()
    try:
        result = gb.execute_user_turn(db, t, srow, body.content, body.branch_id)
    except Exception as e:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            str(e)[:1500],
        ) from e
    if result.get("error"):
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(result["error"])[:2000])
    db.refresh(t)
    arts = db.query(ArtifactRecord).filter(ArtifactRecord.thread_id == t.id).all()
    return {
        "thread_id": t.id,
        "branch_id": result.get("branch_id", t.active_branch_id),
        "phase": result["phase"],
        "messages": result.get("messages", []),
        "quick_replies": result.get("quick_replies", []),
        "planning_summary": result.get("planning_summary"),
        "artifacts": [
            {
                "id": a.id,
                "kind": a.kind,
                "filename": a.filename,
                "download_path": f"/v1/artifacts/{a.id}/download",
            }
            for a in arts
        ],
        "ui_events": result.get("ui_events", []),
        "final_pdf_path": result.get("final_pdf_path"),
        "stream_planning_live": bool(result.get("stream_planning_live", False)),
    }


@router.post("/{thread_id}/messages/{message_id}/regenerate")
def regenerate(
    thread_id: str,
    message_id: str,
    body: RegenerateBody | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = _thread(db, user, thread_id)
    srow = _settings_row(db, user)
    bid = _branch_id(t, body.branch_id if body else None)
    eng = gb.get_engine(db, t, bid, srow)
    if eng.state.internal_busy:
        raise HTTPException(status.HTTP_409_CONFLICT, "Busy")
    result = gb.execute_regenerate(db, t, srow, body.branch_id if body else None)
    if result.get("error"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, result["error"])
    return {
        "thread_id": t.id,
        "branch_id": result.get("branch_id", t.active_branch_id),
        "phase": result["phase"],
        "messages": result.get("messages", []),
        "quick_replies": result.get("quick_replies", []),
        "planning_summary": result.get("planning_summary"),
        "ui_events": result.get("ui_events", []),
        "stream_planning_live": bool(result.get("stream_planning_live", False)),
    }


@router.post("/{thread_id}/messages/{message_id}/edit", status_code=201)
def edit_message_fork(
    thread_id: str,
    message_id: str,
    body: EditMessageBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = _thread(db, user, thread_id)
    srow = _settings_row(db, user)
    parent = body.branch_id or t.active_branch_id
    out = gb.fork_from_user_edit(db, t, srow, parent, message_id, body.new_content)
    if out.get("error"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            out.get("error", "fork_failed"),
        )
    return out


@router.get("/{thread_id}/planning/jobs/{job_id}")
def poll_job(
    thread_id: str,
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _thread(db, user, thread_id)
    if not job_svc.assert_job_user(job_id, user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    j = job_svc.get_job(job_id)
    if not j:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    st = j.get("status", "unknown")
    payload: dict = {
        "job_id": job_id,
        "state": st if st in {"queued", "running", "completed", "failed"} else "running",
        "phase": None,
        "progress": {},
        "events": [],
        "result": None,
    }
    if st in ("queued", "running"):
        payload["ui_events"] = list(j.get("live_ui_events") or [])
    if st == "completed":
        res = j.get("result") or {}
        payload["result"] = res
        if isinstance(res, dict) and res.get("phase") is not None:
            payload["phase"] = res.get("phase")
        if isinstance(res, dict):
            payload["ui_events"] = res.get("ui_events") or []
    if st == "failed":
        payload["error"] = j.get("error", "failed")
        payload["ui_events"] = list(j.get("live_ui_events") or [])
    return payload


@router.get("/{thread_id}/report")
def get_report(
    thread_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = _thread(db, user, thread_id)
    srow = _settings_row(db, user)
    eng = gb.get_engine(db, t, t.active_branch_id, srow)
    if not eng.state.report_package:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not generated yet")
    return eng.state.report_package


@router.get("/{thread_id}/artifacts")
def list_artifacts(
    thread_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = _thread(db, user, thread_id)
    rows = db.query(ArtifactRecord).filter(ArtifactRecord.thread_id == t.id).all()
    return {
        "items": [
            {
                "id": r.id,
                "kind": r.kind,
                "filename": r.filename,
                "mime_type": r.mime_type,
                "size_bytes": r.size_bytes,
                "created_at": r.created_at.isoformat(),
                "download_path": f"/v1/artifacts/{r.id}/download",
            }
            for r in rows
        ]
    }


@router.get("/{thread_id}/export")
def export_thread(
    thread_id: str,
    fmt: str = "json",
    branch_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = _thread(db, user, thread_id)
    bid = branch_id or t.active_branch_id
    msgs = (
        db.query(Message)
        .filter(Message.thread_id == t.id, Message.branch_id == bid)
        .order_by(Message.created_at.asc())
        .all()
    )
    data = {
        "thread": {"id": t.id, "title": t.title, "phase": t.phase, "branch_id": bid},
        "messages": [
            {"role": m.role, "content": m.content, "agent": m.agent} for m in msgs
        ],
    }
    if fmt == "markdown":
        lines = [f"# {t.title}", ""]
        for m in msgs:
            who = (m.agent or m.role).title()
            lines.append(f"## {who}")
            lines.append(m.content or "")
            lines.append("")
        return Response(
            content="\n".join(lines),
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{t.id[:8]}.md"'},
        )
    return Response(
        content=json.dumps(data, indent=2, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{t.id[:8]}.json"'},
    )


@router.post("/{thread_id}/development/messages")
def post_development_message(
    thread_id: str,
    body: DevMessageBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = _thread(db, user, thread_id)
    srow = _settings_row(db, user)
    out = gb.development_answer(db, t, srow, body.content, body.branch_id)
    if out.get("error") == "forbidden":
        raise HTTPException(status.HTTP_403_FORBIDDEN, out.get("detail", "Forbidden"))
    if out.get("error"):
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(out.get("detail")))
    return {"message": out["message"], "citations": []}
