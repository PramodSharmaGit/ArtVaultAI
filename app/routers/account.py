from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import ensure_profile, get_current_user
from app.db import get_db
from app.models import TIER_MEMBER, Profile

router = APIRouter()


@router.post("/upgrade")
def upgrade(request: Request, db: Session = Depends(get_db)):
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
    return RedirectResponse("/#pricing", status_code=303)
