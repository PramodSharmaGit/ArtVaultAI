import logging

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Asset
from app.routers import catalog
from app.templating import BASE_DIR, templates

logger = logging.getLogger(__name__)

app = FastAPI(title="The Art Vault")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(catalog.router)

@app.get("/", response_class=HTMLResponse)
def landing(request: Request, db: Session = Depends(get_db)):
    try:
        assets = db.scalars(select(Asset).order_by(Asset.id).limit(6)).all()
    except SQLAlchemyError:
        # The landing page is public; keep it up even if the catalog can't load.
        logger.exception("Could not load catalog preview")
        assets = []
    return templates.TemplateResponse(request, "landing.html", {"assets": assets})
