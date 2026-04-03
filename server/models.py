"""SQLAlchemy models for users, permissions, feedback, playlists, comments, and invitations."""

import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    picture_url: Mapped[str | None] = mapped_column(String(2048))
    password_hash: Mapped[str | None] = mapped_column(String(255))  # null for OAuth-only
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    role: Mapped[str] = mapped_column(String(20), default="user")  # "user" or "admin"
    theme: Mapped[str] = mapped_column(String(20), default="retro")  # "retro", "spotify", "disco"
    dark_mode: Mapped[str] = mapped_column(String(20), default="dark")  # "dark", "day", "night"
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")  # e.g. "en", "vi", "zh"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    invited_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    permissions: Mapped["UserPermissions"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    invited_by: Mapped["User | None"] = relationship(remote_side="User.id", foreign_keys=[invited_by_id])

    def to_dict(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "name": self.name,
            "picture_url": self.picture_url,
            "role": self.role,
            "theme": self.theme,
            "dark_mode": self.dark_mode,
            "preferred_language": self.preferred_language,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "invited_by_id": str(self.invited_by_id) if self.invited_by_id else None,
        }


class UserPermissions(Base):
    __tablename__ = "user_permissions"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    max_karaoke_per_day: Mapped[int] = mapped_column(Integer, default=5)
    max_subtitled_per_day: Mapped[int] = mapped_column(Integer, default=15)
    max_queue_length: Mapped[int] = mapped_column(Integer, default=10)
    can_download_karaoke: Mapped[bool] = mapped_column(Boolean, default=True)
    can_download_instrumental: Mapped[bool] = mapped_column(Boolean, default=True)
    can_download_vocals: Mapped[bool] = mapped_column(Boolean, default=True)
    can_delete_library: Mapped[bool] = mapped_column(Boolean, default=False)
    can_share_library: Mapped[bool] = mapped_column(Boolean, default=True)
    max_invitations: Mapped[int] = mapped_column(Integer, default=5)  # 0 = unlimited
    can_request_songs: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="permissions")

    def to_dict(self):
        return {
            "max_karaoke_per_day": self.max_karaoke_per_day,
            "max_subtitled_per_day": self.max_subtitled_per_day,
            "max_queue_length": self.max_queue_length,
            "can_download_karaoke": self.can_download_karaoke,
            "can_download_instrumental": self.can_download_instrumental,
            "can_download_vocals": self.can_download_vocals,
            "can_delete_library": self.can_delete_library,
            "can_share_library": self.can_share_library,
            "max_invitations": self.max_invitations,
            "can_request_songs": self.can_request_songs,
        }


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    screenshot_path: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(20), default="new")  # "new", "reviewed", "resolved"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped["User"] = relationship()

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "user_name": self.user.name if self.user else None,
            "user_email": self.user.email if self.user else None,
            "subject": self.subject,
            "description": self.description,
            "screenshot_path": self.screenshot_path,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_user_job_vote"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    value: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # +1 or -1
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped["User"] = relationship()
    items: Mapped[list["PlaylistItem"]] = relationship(back_populates="playlist", cascade="all, delete-orphan", order_by="PlaylistItem.position")

    def to_dict(self, include_items=False):
        d = {
            "id": str(self.id),
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "item_count": len(self.items) if self.items else 0,
        }
        if include_items:
            d["items"] = [item.to_dict() for item in (self.items or [])]
        return d


class PlaylistItem(Base):
    __tablename__ = "playlist_items"
    __table_args__ = (
        UniqueConstraint("playlist_id", "job_id", name="uq_playlist_job"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    playlist_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("playlists.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    playlist: Mapped["Playlist"] = relationship(back_populates="items")

    def to_dict(self):
        return {
            "id": str(self.id),
            "job_id": self.job_id,
            "position": self.position,
            "added_at": self.added_at.isoformat() if self.added_at else None,
        }


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped["User"] = relationship()

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "user_name": self.user.name if self.user else None,
            "user_picture": self.user.picture_url if self.user else None,
            "job_id": self.job_id,
            "text": self.text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LibraryItem(Base):
    """A song in the library. Created when a production job completes."""
    __tablename__ = "library_items"

    job_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str | None] = mapped_column(String(512))
    artist: Mapped[str | None] = mapped_column(String(255))
    year: Mapped[str | None] = mapped_column(String(10))
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    analysis_text: Mapped[str | None] = mapped_column(Text)
    analysis_song_info: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Extended fields for library listing (replaces job.json scanning)
    url: Mapped[str | None] = mapped_column(String(512))
    mode: Mapped[str | None] = mapped_column(String(20))  # karaoke/subtitled/both
    languages: Mapped[str | None] = mapped_column(Text)  # JSON list
    thumbnail: Mapped[str | None] = mapped_column(String(512))
    channel: Mapped[str | None] = mapped_column(String(255))
    upload_date: Mapped[str | None] = mapped_column(String(20))
    categories: Mapped[str | None] = mapped_column(Text)  # JSON list
    tags: Mapped[str | None] = mapped_column(Text)  # JSON list
    finished_at: Mapped[str | None] = mapped_column(String(50))
    audio_duration: Mapped[float | None] = mapped_column(sa.Float)
    language_detected: Mapped[str | None] = mapped_column(String(10))
    status: Mapped[str | None] = mapped_column(String(20), default="done")
    added_by: Mapped[str | None] = mapped_column(String(255))
    added_by_id: Mapped[str | None] = mapped_column(String(255))
    error: Mapped[str | None] = mapped_column(Text)
    file_size_bytes: Mapped[int | None] = mapped_column(sa.BigInteger)
    lyrics: Mapped[str | None] = mapped_column(Text)  # JSON array of {text, start, end}
    subtitles: Mapped[str | None] = mapped_column(Text)  # JSON: {"en": "srt content", "vi": "srt content"}

    def to_dict(self):
        return {
            "job_id": self.job_id,
            "title": self.title,
            "artist": self.artist,
            "year": self.year,
            "view_count": self.view_count,
            "analysis_text": self.analysis_text,
            "analysis_song_info": self.analysis_song_info,
        }

    def to_library_dict(self):
        return {
            "id": self.job_id,
            "title": self.title or "Unknown",
            "artist": self.artist or "",
            "url": self.url,
            "mode": self.mode or "karaoke",
            "languages": json.loads(self.languages) if self.languages else [],
            "thumbnail": self.thumbnail,
            "channel": self.channel,
            "upload_date": self.upload_date,
            "categories": json.loads(self.categories) if self.categories else [],
            "tags": json.loads(self.tags) if self.tags else [],
            "finished_at": self.finished_at,
            "audio_duration": self.audio_duration,
            "year": self.year,
            "language": self.language_detected,
            "added_by": self.added_by,
            "added_by_id": self.added_by_id,
            "view_count": self.view_count or 0,
        }


def _invite_expiry():
    return datetime.now(timezone.utc) + timedelta(days=7)


class Invitation(Base):
    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inviter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False, default=lambda: secrets.token_urlsafe(32))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # "pending", "accepted"
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_invite_expiry)
    accepted_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    inviter: Mapped["User"] = relationship(foreign_keys=[inviter_id])
    accepted_by: Mapped["User | None"] = relationship(foreign_keys=[accepted_by_id])

    def is_valid(self) -> bool:
        return self.status == "pending" and datetime.now(timezone.utc) < self.expires_at

    def to_dict(self):
        return {
            "id": str(self.id),
            "email": self.email,
            "token": self.token,
            "inviter_name": self.inviter.name if self.inviter else None,
            "status": self.status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "accepted_by_id": str(self.accepted_by_id) if self.accepted_by_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WishlistItem(Base):
    __tablename__ = "wishlist_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str | None] = mapped_column(String(512))
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    artist: Mapped[str | None] = mapped_column(String(255))
    thumbnail: Mapped[str | None] = mapped_column(String(512))
    note: Mapped[str | None] = mapped_column(Text)
    mode: Mapped[str | None] = mapped_column(String(20), default="karaoke")  # "karaoke", "subtitled", "both"
    languages: Mapped[str | None] = mapped_column(Text)  # JSON array: ["en", "vi"]
    status: Mapped[str] = mapped_column(String(20), default="open")  # "open", "queued", "fulfilled", "rejected"
    fulfilled_by_job_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user: Mapped["User"] = relationship()

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "user_name": self.user.name if self.user else None,
            "url": self.url,
            "title": self.title,
            "artist": self.artist,
            "thumbnail": self.thumbnail,
            "note": self.note,
            "mode": self.mode or "karaoke",
            "languages": json.loads(self.languages) if self.languages else [],
            "status": self.status,
            "fulfilled_by_job_id": self.fulfilled_by_job_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WishlistVote(Base):
    __tablename__ = "wishlist_votes"
    __table_args__ = (
        UniqueConstraint("user_id", "wishlist_item_id", name="uq_user_wishlist_vote"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    wishlist_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("wishlist_items.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class ActivityLog(Base):
    """Append-only activity log for admin monitoring."""
    __tablename__ = "activity_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_name: Mapped[str] = mapped_column(String(255), default="Anonymous")
    event_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)


class AppConfig(Base):
    """Key-value store for system config (settings, prompts, stats, queue)."""
    __tablename__ = "app_config"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
