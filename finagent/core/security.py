from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from finagent.core.config import get_settings
from finagent.db.models import User
from finagent.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(subject: str) -> str:
    s = get_settings()
    return jwt.encode(
        {
            "sub": subject,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=s.jwt_expire_minutes),
        },
        s.secret_key,
        algorithm="HS256",
    )


def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        subject = jwt.decode(token, get_settings().secret_key, algorithms=["HS256"])["sub"]
    except (jwt.InvalidTokenError, KeyError) as exc:
        raise HTTPException(401, "Invalid or expired token") from exc
    user = db.scalar(select(User).where(User.id == subject))
    if not user:
        raise HTTPException(401, "User no longer exists")
    return user
