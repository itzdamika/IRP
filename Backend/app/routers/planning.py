from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..deps import get_current_user
from ..db.models import User
from .threads import _thread
from ..services import jobs as job_svc

router = APIRouter(prefix="/threads", tags=["planning"])


@router.post("/{thread_id}/planning/jobs", status_code=202)
def start_planning_job(
    thread_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Explicitly run governance cycle when thread is stuck in PLANNING (or to retry)."""
    _thread(db, user, thread_id)
    job_id = job_svc.submit_planning_cycle(thread_id, user.id)
    return Response(
        content=json.dumps(
            {
                "job_id": job_id,
                "status_url": f"/v1/threads/{thread_id}/planning/jobs/{job_id}",
                "ws_url": f"/v1/ws/jobs/{job_id}",
                "poll_after_ms": 600,
            }
        ),
        media_type="application/json",
    )
