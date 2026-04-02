"""Authentication utilities: JWT, password hashing, OAuth, FastAPI dependencies."""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Cookie, Depends, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserPermissions

JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 72
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")


# --- Password helpers ---

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# --- JWT helpers ---

def create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    return jwt.encode({"sub": user_id, "exp": expire}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> str | None:
    """Returns user_id or None if invalid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# --- FastAPI dependencies ---

def get_current_user(
    access_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
) -> User:
    """Dependency: returns authenticated User or raises 401."""
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user_id = decode_token(access_token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_optional_user(
    access_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
) -> User | None:
    """Dependency: returns User if authenticated, None otherwise. No 401."""
    if not access_token:
        return None
    user_id = decode_token(access_token)
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Dependency: returns User if admin, raises 403 otherwise."""
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


def is_admin(user: User | None) -> bool:
    """Check if a user has admin role. Safe to call with None."""
    return user is not None and user.role == "admin"


# --- User creation helpers ---

def create_user_with_permissions(db: Session, email: str, name: str,
                                  password: str | None = None,
                                  google_id: str | None = None,
                                  picture_url: str | None = None,
                                  invited_by_id: str | None = None) -> User:
    """Create a new user with default permissions. Auto-promotes to admin if ADMIN_EMAIL matches."""
    role = "admin" if (ADMIN_EMAIL and email.lower() == ADMIN_EMAIL.lower()) else "user"

    user = User(
        email=email.lower(),
        name=name,
        password_hash=hash_password(password) if password else None,
        google_id=google_id,
        picture_url=picture_url,
        role=role,
        invited_by_id=invited_by_id,
    )
    db.add(user)
    db.flush()

    # Apply admin-configured defaults if settings file exists
    import json
    from pathlib import Path
    _settings_path = Path(__file__).resolve().parent / "output" / "jobs" / "settings.json"
    settings = {}
    if _settings_path.exists():
        try:
            settings = json.loads(_settings_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    perms = UserPermissions(
        user_id=user.id,
        max_karaoke_per_day=settings.get("default_max_karaoke_per_day", 5),
        max_subtitled_per_day=settings.get("default_max_subtitled_per_day", 15),
        max_queue_length=settings.get("default_max_queue_length", 10),
        can_download_karaoke=settings.get("default_can_download_karaoke", True),
        can_download_instrumental=settings.get("default_can_download_instrumental", True),
        can_download_vocals=settings.get("default_can_download_vocals", True),
        can_delete_library=settings.get("default_can_delete_library", False),
        can_share_library=settings.get("default_can_share_library", True),
        max_invitations=settings.get("default_max_invitations", 5),
        can_request_songs=settings.get("default_can_request_songs", True),
    )
    db.add(perms)
    db.commit()
    db.refresh(user)
    return user
