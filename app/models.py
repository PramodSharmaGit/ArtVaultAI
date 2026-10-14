import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

TIER_FREE = "free"
TIER_MEMBER = "member"


class Base(DeclarativeBase):
    pass


class Profile(Base):
    """One row per Supabase Auth user. `id` is the same UUID as auth.users.id."""

    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tier: Mapped[str] = mapped_column(String(10), default=TIER_FREE, server_default=TIER_FREE)
    member_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Asset(Base):
    """A catalog item. `tier_required` is 'free' or 'member'."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(Text)
    age_min: Mapped[int] = mapped_column(Integer)
    age_max: Mapped[int] = mapped_column(Integer)
    materials: Mapped[str] = mapped_column(String(160))
    preview_image_url: Mapped[str] = mapped_column(String(255))
    download_file_url: Mapped[str] = mapped_column(String(255))
    tier_required: Mapped[str] = mapped_column(String(10), default=TIER_FREE, server_default=TIER_FREE)


class Download(Base):
    """One row per completed download. Counting a user's rows enforces the free-tier cap."""

    __tablename__ = "downloads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id"), index=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"))
    downloaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
