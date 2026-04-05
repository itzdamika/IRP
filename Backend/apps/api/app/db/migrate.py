"""One-time backfill after schema changes."""
from __future__ import annotations

import logging

from sqlalchemy import inspect, text

from .models import Branch, Thread
from .session import SessionLocal, engine

_log = logging.getLogger(__name__)


def ensure_branch_extra_column() -> None:
    """Add branches.extra for DBs created before that column existed (create_all skips alters)."""
    try:
        insp = inspect(engine)
        if "branches" not in insp.get_table_names():
            return
        col_names = {c["name"] for c in insp.get_columns("branches")}
        if "extra" in col_names:
            return
        dialect = engine.dialect.name
        with engine.begin() as conn:
            if dialect == "postgresql":
                conn.execute(text("ALTER TABLE branches ADD COLUMN extra JSON"))
            else:
                # SQLite and others: JSON is stored as TEXT
                conn.execute(text("ALTER TABLE branches ADD COLUMN extra TEXT"))
        _log.info("Added missing column branches.extra")
    except Exception:
        _log.exception("Could not ensure branches.extra column")


def backfill_branches() -> None:
    db = SessionLocal()
    try:
        for t in db.query(Thread).all():
            exists = db.query(Branch).filter(Branch.id == t.active_branch_id).first()
            if not exists:
                db.add(
                    Branch(
                        id=t.active_branch_id,
                        thread_id=t.id,
                        label="main",
                        parent_branch_id=None,
                        engine_state_blob=t.engine_state_blob,
                    )
                )
        db.commit()
    finally:
        db.close()
