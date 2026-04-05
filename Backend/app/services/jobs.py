from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from ..db.models import Thread, UserSettingsRow
from ..db.session import SessionLocal

_executor = ThreadPoolExecutor(max_workers=8)
_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}


def _put(job_id: str, **kwargs: Any) -> None:
    with _lock:
        if job_id not in _jobs:
            _jobs[job_id] = {}
        _jobs[job_id].update(kwargs)


def _ws_notify(job_id: str, message: dict[str, Any]) -> None:
    try:
        from . import planning_ws as pws

        pws.notify_job(job_id, message)
    except Exception:
        pass


def sync_live_ui_events(job_id: str, events: list[Any]) -> None:
    """Copy governance UI events into the job for live polling (thread-safe)."""
    snap: list[Any] = []
    for e in events:
        if isinstance(e, dict):
            snap.append(dict(e))
        else:
            snap.append(e)
    _put(job_id, live_ui_events=snap)
    _ws_notify(job_id, {"type": "ui_events", "events": snap})


def get_job(job_id: str) -> dict[str, Any] | None:
    with _lock:
        return _jobs.get(job_id)


def submit_message_turn(
    thread_id: str,
    user_id: str,
    content: str,
    branch_id: str | None,
) -> str:
    from . import governance_bridge as gb

    job_id = str(uuid.uuid4())
    _put(
        job_id,
        status="queued",
        thread_id=thread_id,
        user_id=user_id,
        kind="message",
        result=None,
        error=None,
        live_ui_events=[],
    )

    def work() -> None:
        db = SessionLocal()
        try:
            _put(job_id, status="running")
            t = (
                db.query(Thread)
                .filter(Thread.id == thread_id, Thread.user_id == user_id)
                .first()
            )
            if not t:
                _put(job_id, status="failed", error="thread_not_found")
                _ws_notify(
                    job_id,
                    {
                        "type": "job_state",
                        "state": "failed",
                        "error": "thread_not_found",
                    },
                )
                return
            if t.title == "New chat" and content.strip():
                s = content.strip()
                t.title = s[:100] + ("…" if len(s) > 100 else "")
                db.add(t)
                db.commit()
            srow = (
                db.query(UserSettingsRow)
                .filter(UserSettingsRow.user_id == user_id)
                .first()
            )
            result = gb.execute_user_turn(
                db, t, srow, content, branch_id, stream_job_id=job_id
            )
            if result.get("error"):
                _put(job_id, status="failed", error=result["error"])
                _ws_notify(
                    job_id,
                    {"type": "job_state", "state": "failed", "error": result["error"]},
                )
            else:
                _put(job_id, status="completed", result=result)
                _ws_notify(
                    job_id,
                    {
                        "type": "job_state",
                        "state": "completed",
                        "phase": result.get("phase"),
                    },
                )
        except Exception as e:
            _put(job_id, status="failed", error=str(e))
            _ws_notify(
                job_id, {"type": "job_state", "state": "failed", "error": str(e)}
            )
        finally:
            db.close()

    _executor.submit(work)
    return job_id


def submit_planning_cycle(thread_id: str, user_id: str) -> str:
    from . import governance_bridge as gb

    job_id = str(uuid.uuid4())
    _put(
        job_id,
        status="queued",
        thread_id=thread_id,
        user_id=user_id,
        kind="planning",
        result=None,
        error=None,
        live_ui_events=[],
    )

    def work() -> None:
        db = SessionLocal()
        try:
            _put(job_id, status="running")
            t = (
                db.query(Thread)
                .filter(Thread.id == thread_id, Thread.user_id == user_id)
                .first()
            )
            if not t:
                _put(job_id, status="failed", error="thread_not_found")
                _ws_notify(
                    job_id,
                    {
                        "type": "job_state",
                        "state": "failed",
                        "error": "thread_not_found",
                    },
                )
                return
            srow = (
                db.query(UserSettingsRow)
                .filter(UserSettingsRow.user_id == user_id)
                .first()
            )
            result = gb.run_governance_only(
                db, t, srow, None, stream_job_id=job_id
            )
            if result.get("error"):
                _put(
                    job_id,
                    status="failed",
                    error=result.get("error"),
                    detail=result.get("detail"),
                )
                _ws_notify(
                    job_id,
                    {
                        "type": "job_state",
                        "state": "failed",
                        "error": result.get("error"),
                    },
                )
            else:
                _put(job_id, status="completed", result=result)
                _ws_notify(
                    job_id,
                    {
                        "type": "job_state",
                        "state": "completed",
                        "phase": result.get("phase"),
                    },
                )
        except Exception as e:
            _put(job_id, status="failed", error=str(e))
            _ws_notify(
                job_id, {"type": "job_state", "state": "failed", "error": str(e)}
            )
        finally:
            db.close()

    _executor.submit(work)
    return job_id


def assert_job_user(job_id: str, user_id: str) -> bool:
    j = get_job(job_id)
    return bool(j and j.get("user_id") == user_id)
