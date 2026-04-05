from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db.models import User
from ..db.session import get_db
from ..deps import get_current_user

router = APIRouter(tags=["users"])


class UserOut(BaseModel):
    id: str
    email: str
    display_name: str
    avatar_url: str | None
    created_at: str

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    display_name: str | None = Field(None, max_length=255)
    avatar_url: str | None = Field(None, max_length=512)


@router.get("/me", response_model=UserOut)
def read_me(user: User = Depends(get_current_user)):
    return UserOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        created_at=user.created_at.isoformat(),
    )


@router.patch("/me", response_model=UserOut)
def patch_me(
    body: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.display_name is not None:
        user.display_name = body.display_name
    if body.avatar_url is not None:
        user.avatar_url = body.avatar_url
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        created_at=user.created_at.isoformat(),
    )
