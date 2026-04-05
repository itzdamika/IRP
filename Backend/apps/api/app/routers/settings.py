from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db.models import Thread, User, UserSettingsRow
from ..db.session import get_db
from ..deps import get_current_user
from ..services import governance_bridge as gb

router = APIRouter(prefix="/settings", tags=["settings"])


class UserSettingsOut(BaseModel):
    pass_threshold: float = Field(ge=7.0, le=10.0)
    max_planning_rounds: int = Field(ge=1, le=50)
    max_requirement_hops: int = Field(ge=1, le=30)
    report_depth: str
    thinking_enabled: bool
    show_internal_panels: bool
    theme: str


def _get_or_create_settings(db: Session, user: User) -> UserSettingsRow:
    row = db.query(UserSettingsRow).filter(UserSettingsRow.user_id == user.id).first()
    if not row:
        row = UserSettingsRow(user_id=user.id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _row_to_out(row: UserSettingsRow) -> UserSettingsOut:
    return UserSettingsOut(
        pass_threshold=row.pass_threshold,
        max_planning_rounds=row.max_planning_rounds,
        max_requirement_hops=row.max_requirement_hops,
        report_depth=row.report_depth,
        thinking_enabled=row.thinking_enabled,
        show_internal_panels=row.show_internal_panels,
        theme=row.theme,
    )


@router.get("", response_model=UserSettingsOut)
def get_settings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = _get_or_create_settings(db, user)
    return _row_to_out(row)


@router.put("", response_model=UserSettingsOut)
def put_settings(
    body: UserSettingsOut,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = _get_or_create_settings(db, user)
    row.pass_threshold = body.pass_threshold
    row.max_planning_rounds = body.max_planning_rounds
    row.max_requirement_hops = body.max_requirement_hops
    row.report_depth = body.report_depth
    row.thinking_enabled = body.thinking_enabled
    row.show_internal_panels = body.show_internal_panels
    row.theme = body.theme
    db.add(row)
    db.commit()
    db.refresh(row)
    for tid in list(gb._engines.keys()):
        t = db.query(Thread).filter(Thread.id == tid, Thread.user_id == user.id).first()
        if t:
            gb.drop_engine_cache(tid)
    return _row_to_out(row)
