from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from ..core.security import create_access_token, hash_password, verify_password
from ..db.models import User, UserSettingsRow
from ..db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(default="", max_length=255)


class LoginBody(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(body: RegisterBody, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email.lower()).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")
    user = User(
        email=body.email.lower(),
        hashed_password=hash_password(body.password),
        display_name=body.display_name or body.email.split("@")[0],
    )
    db.add(user)
    db.flush()
    db.add(
        UserSettingsRow(
            user_id=user.id,
        )
    )
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer", "user_id": user.id}


@router.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer", "user_id": user.id}
