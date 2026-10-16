import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import ensure_profile, get_current_user
from app.activity_content import ACTIVITY_GUIDES, ACTIVITY_OUTCOMES
from app.db import get_db
from app.models import FREE_DOWNLOAD_CAP, TIER_FREE, TIER_MEMBER, Asset, Download, Profile
from app.templating import BASE_DIR, templates

logger = logging.getLogger(__name__)
router = APIRouter()

# Downloadable files live outside static/, so only the gated download route can serve them.
PRIVATE_DIR = (BASE_DIR / "private").resolve()


def search_assets(db: Session, q: str, tier: str, age: int | None) -> list[Asset]:
    stmt = select(Asset).order_by(Asset.id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Asset.title.ilike(like), Asset.description.ilike(like), Asset.materials.ilike(like)))
    if tier in (TIER_FREE, TIER_MEMBER):
        stmt = stmt.where(Asset.tier_required == tier)
    if age is not None:
        stmt = stmt.where(Asset.age_min <= age, Asset.age_max >= age)
    return list(db.scalars(stmt))


@router.get("/catalog", response_class=HTMLResponse)
def catalog(request: Request, q: str = "", tier: str = "", age: str = "", db: Session = Depends(get_db)):
    q = q.strip()[:100]
    age_value = int(age) if age.isdigit() and 0 < int(age) < 100 else None
    load_failed = False
    try:
        assets = search_assets(db, q, tier, age_value)
    except SQLAlchemyError:
        logger.exception("Could not load catalog")
        assets, load_failed = [], True

    context = {"assets": assets, "q": q, "tier": tier, "age": age_value, "load_failed": load_failed}
    # htmx asks for just the results; a normal visit gets the whole page.
    template = "_catalog_results.html" if request.headers.get("HX-Request") else "catalog.html"
    return templates.TemplateResponse(request, template, context)


def download_block_reason(tier: str, asset_tier: str, used: int) -> str | None:
    """Why this user can't download this asset right now, or None if they can."""
    if tier == TIER_MEMBER:
        return None
    if asset_tier == TIER_MEMBER:
        return "This activity is for members only."
    if used >= FREE_DOWNLOAD_CAP:
        return f"You've used all {FREE_DOWNLOAD_CAP} of your free downloads."
    return None


def downloads_used(db: Session, user_id) -> int:
    return db.scalar(select(func.count()).select_from(Download).where(Download.user_id == user_id)) or 0


def private_file(asset: Asset):
    """The asset's file on disk, or None. Never lets a path escape the private folder."""
    path = (PRIVATE_DIR / asset.download_file_url).resolve()
    return path if PRIVATE_DIR in path.parents and path.is_file() else None


def get_asset_or_404(db: Session, asset_id: int) -> Asset:
    try:
        asset = db.get(Asset, asset_id)
    except SQLAlchemyError:
        logger.exception("Could not load asset %s", asset_id)
        raise HTTPException(503, "Activities are taking a short break. Please try again in a moment.")
    if asset is None:
        raise HTTPException(404, "Activity not found")
    return asset


def render_detail(request: Request, db: Session, asset: Asset, status_code: int = 200, error: str = ""):
    user = get_current_user(request)
    tier, used = None, 0
    if user:
        try:
            ensure_profile(db, user.id)
            profile = db.get(Profile, user.id)
            tier = profile.tier if profile else TIER_FREE
            used = downloads_used(db, user.id)
        except SQLAlchemyError:
            logger.exception("Could not load account for %s", user.id)
            tier = TIER_FREE
    context = {
        "asset": asset, "error": error, "tier": tier, "used": used, "cap": FREE_DOWNLOAD_CAP,
        "guide": ACTIVITY_GUIDES.get(asset.title),
        "outcome": ACTIVITY_OUTCOMES.get(asset.title),
        "block_reason": download_block_reason(tier, asset.tier_required, used) if user else None,
    }
    return templates.TemplateResponse(request, "asset_detail.html", context, status_code=status_code)


@router.get("/assets/{asset_id}", response_class=HTMLResponse)
def asset_detail(request: Request, asset_id: int, db: Session = Depends(get_db)):
    return render_detail(request, db, get_asset_or_404(db, asset_id))


@router.post("/assets/{asset_id}/download")
def download(request: Request, asset_id: int, db: Session = Depends(get_db)):
    """The real access control: tier and download cap are checked here, on the server."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(f"/login?next=/assets/{asset_id}", status_code=303)
    asset = get_asset_or_404(db, asset_id)

    try:
        ensure_profile(db, user.id)
        # Lock this user's profile row so two simultaneous requests can't both slip under the cap.
        profile = db.scalar(select(Profile).where(Profile.id == user.id).with_for_update())
        tier = profile.tier if profile else TIER_FREE
        reason = download_block_reason(tier, asset.tier_required, downloads_used(db, user.id))
        if reason:
            db.rollback()
            return render_detail(request, db, asset, status_code=403, error=reason)

        path = private_file(asset)
        if path is None:
            db.rollback()
            logger.error("Missing download file for asset %s", asset.id)
            return render_detail(request, db, asset, status_code=404,
                                 error="Sorry, this file isn't available right now.")

        db.add(Download(user_id=user.id, asset_id=asset.id))
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Download failed for asset %s", asset_id)
        raise HTTPException(503, "Downloads are taking a short break. Please try again in a moment.")
    return FileResponse(path, filename=path.name)
