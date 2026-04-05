"""Fan-out planning / job UI events to WebSocket subscribers (thread-safe with asyncio)."""
from __future__ import annotations

import asyncio
import threading
from typing import Any, Dict, List

_main_loop: asyncio.AbstractEventLoop | None = None
_tlock = threading.Lock()
_subscribers: Dict[str, List[asyncio.Queue]] = {}


def set_main_loop(loop: asyncio.AbstractEventLoop | None) -> None:
    global _main_loop
    _main_loop = loop


def subscribe(job_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=512)
    with _tlock:
        _subscribers.setdefault(job_id, []).append(q)
    return q


def unsubscribe(job_id: str, q: asyncio.Queue) -> None:
    with _tlock:
        lst = _subscribers.get(job_id)
        if not lst:
            return
        if q in lst:
            lst.remove(q)
        if not lst:
            del _subscribers[job_id]


def notify_job(job_id: str, message: Dict[str, Any]) -> None:
    loop = _main_loop
    if loop is None:
        return
    with _tlock:
        queues = list(_subscribers.get(job_id, []))

    async def _push() -> None:
        for q in queues:
            try:
                q.put_nowait(message)
            except asyncio.QueueFull:
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    q.put_nowait(message)
                except asyncio.QueueFull:
                    pass

    try:
        asyncio.run_coroutine_threadsafe(_push(), loop)
    except RuntimeError:
        pass
