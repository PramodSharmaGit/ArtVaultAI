import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import TIER_FREE, TIER_MEMBER, Asset
from app.templating import templates

logger = logging.getLogger(__name__)
router = APIRouter()


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
