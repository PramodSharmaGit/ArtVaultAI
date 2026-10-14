"""Supabase Auth helpers. Tokens live in HttpOnly cookies; Supabase verifies them on each request."""
import logging
import os
import uuid
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv
from fastapi import Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from supabase import AuthError, Client, create_client

from app.db import SessionLocal
from app.models import Profile

load_dotenv()
logger = logging.getLogger(__name__)

ACCESS_COOKIE = "av_access"
REFRESH_COOKIE = "av_refresh"
REFRESH_MAX_AGE = 60 * 60 * 24 * 7


@dataclass
class CurrentUser:
    id: uuid.UUID
    email: str
    name: str = ""


def supabase_client() -> Client:
    """A fresh client per call, so one visitor's session is never shared with another's."""
    url, key = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env.")
    return create_client(url, key)


def get_current_user(request: Request) -> CurrentUser | None:
    """The logged-in user for this request, or None. Cached on the request."""
    if hasattr(request.state, "user"):
        return request.state.user
    request.state.user = _lookup_user(request)
    return request.state.user


def _lookup_user(request: Request) -> CurrentUser | None:
    access = request.cookies.get(ACCESS_COOKIE)
    refresh = request.cookies.get(REFRESH_COOKIE)
    if not access and not refresh:
        return None
    client = supabase_client()
    try:
        if access:
            try:
                user = client.auth.get_user(access).user
                if user:
                    return _to_current_user(user)
            except AuthError:
                pass  # expired or invalid: fall through to the refresh token
        if refresh:
            session = client.auth.refresh_session(refresh).session
            if session and session.user:
                request.state.new_session = session
                return _to_current_user(session.user)
    except AuthError:
        request.state.clear_cookies = True
    except httpx.HTTPError:
        logger.exception("Could not reach Supabase Auth")
    return None


def _to_current_user(user) -> CurrentUser:
    name = (user.user_metadata or {}).get("full_name") or ""
    return CurrentUser(uuid.UUID(user.id), user.email or "", name)


def get_user_tier(request: Request) -> str | None:
    """The logged-in user's tier ('free' or 'member'), or None if logged out or unavailable."""
    if hasattr(request.state, "tier"):
        return request.state.tier
    user = get_current_user(request)
    request.state.tier = None
    if user:
        try:
            with SessionLocal() as db:
                profile = db.get(Profile, user.id)
                request.state.tier = profile.tier if profile else None
        except SQLAlchemyError:
            logger.exception("Could not load tier for %s", user.id)
    return request.state.tier


def set_session_cookies(response: Response, session, secure: bool) -> None:
    opts = {"httponly": True, "samesite": "lax", "secure": secure}
    response.set_cookie(ACCESS_COOKIE, session.access_token, max_age=session.expires_in or 3600, **opts)
    response.set_cookie(REFRESH_COOKIE, session.refresh_token, max_age=REFRESH_MAX_AGE, **opts)


def clear_session_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE)
    response.delete_cookie(REFRESH_COOKIE)


def apply_cookie_updates(request: Request, response: Response) -> None:
    """Called after every request: save a refreshed session, or drop dead cookies."""
    session = getattr(request.state, "new_session", None)
    if session:
        set_session_cookies(response, session, secure=request.url.scheme == "https")
    elif getattr(request.state, "clear_cookies", False):
        clear_session_cookies(response)


def ensure_profile(db: Session, user_id: uuid.UUID) -> None:
    """Create the user's profile row (free tier) if it doesn't exist yet."""
    try:
        if db.get(Profile, user_id) is None:
            db.add(Profile(id=user_id))
            db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Could not create profile for %s", user_id)
