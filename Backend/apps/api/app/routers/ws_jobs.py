"""WebSocket stream for live planning UI events tied to a background job."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from ..db.session import SessionLocal
from ..deps import user_from_token
from ..services import jobs as job_svc
from ..services import planning_ws

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/jobs/{job_id}")
async def job_events_ws(
    websocket: WebSocket,
    job_id: str,
    token: str | None = Query(None, description="JWT (same as Authorization bearer)"),
):
    db = SessionLocal()
    try:
        user = user_from_token(db, token or "")
        if not user or not job_svc.assert_job_user(job_id, user.id):
            await websocket.close(code=4403)
            return
        await websocket.accept()
        q = planning_ws.subscribe(job_id)
        try:
            snap = job_svc.get_job(job_id)
            if snap:
                await websocket.send_json(
                    {
                        "type": "ui_events",
                        "events": list(snap.get("live_ui_events") or []),
                    }
                )
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=60.0)
                except asyncio.TimeoutError:
                    await websocket.send_json({"type": "ping"})
                    continue
                await websocket.send_json(msg)
                if msg.get("type") == "job_state" and msg.get("state") in (
                    "completed",
                    "failed",
                ):
                    break
        except WebSocketDisconnect:
            pass
        finally:
            planning_ws.unsubscribe(job_id, q)
    finally:
        db.close()
