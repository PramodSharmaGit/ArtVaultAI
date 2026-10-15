import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import ensure_profile, get_current_user, safe_next
from app.db import get_db
from app.models import FREE_DOWNLOAD_CAP, TIER_FREE, TIER_MEMBER, Asset, Download, Profile
from app.routers.catalog import downloads_used
from app.templating import templates

logger = logging.getLogger(__name__)
router = APIRouter()

HISTORY_LIMIT = 20


@router.get("/account", response_class=HTMLResponse)
def account(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/login?next=/account", status_code=303)

    tier, member_since, used, history, load_failed = TIER_FREE, None, 0, [], False
    try:
        ensure_profile(db, user.id)
        profile = db.get(Profile, user.id)
        if profile:
            tier, member_since = profile.tier, profile.member_since
        used = downloads_used(db, user.id)
        history = db.execute(
            select(Asset.id, Asset.title, Download.downloaded_at)
            .join(Asset, Asset.id == Download.asset_id)
            .where(Download.user_id == user.id)
            .order_by(Download.downloaded_at.desc())
            .limit(HISTORY_LIMIT)
        ).all()
    except SQLAlchemyError:
        logger.exception("Could not load account for %s", user.id)
        load_failed = True

    context = {
        "tier": tier, "member_since": member_since, "used": used, "cap": FREE_DOWNLOAD_CAP,
        "remaining": max(FREE_DOWNLOAD_CAP - used, 0), "history": history, "load_failed": load_failed,
    }
    return templates.TemplateResponse(request, "account.html", context)


@router.post("/upgrade")
def upgrade(request: Request, next: str = Form("/#pricing"), db: Session = Depends(get_db)):
    """Demo upgrade: no payment, just flips the user's tier to member."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/signup", status_code=303)

    ensure_profile(db, user.id)
    profile = db.get(Profile, user.id)
    if profile and profile.tier != TIER_MEMBER:
        profile.tier = TIER_MEMBER
        profile.member_since = datetime.now(timezone.utc)
        db.commit()
    return RedirectResponse(safe_next(next), status_code=303)
