from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from finagent.core.security import create_token, hash_password, verify_password
from finagent.db.models import User
from finagent.db.session import get_db

router = APIRouter(prefix="/auth", tags=["authentication"])


class Signup(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


@router.post("/signup", status_code=201)
def signup(body: Signup, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email.lower())):
        raise HTTPException(409, "Email already registered")
    user = User(email=body.email.lower(), password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    return {"access_token": create_token(user.id), "token_type": "bearer"}


@router.post("/token")
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username.lower()))
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_token(user.id), "token_type": "bearer"}
