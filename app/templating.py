from pathlib import Path
from datetime import datetime, timezone

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.auth import get_current_user, get_user_tier

BASE_DIR = Path(__file__).resolve().parent


def user_context(request: Request) -> dict:
    """Makes `current_user` and `user_tier` available in every template (the nav uses them)."""
    return {"current_user": get_current_user(request), "user_tier": get_user_tier(request), "current_year": datetime.now(timezone.utc).year}


templates = Jinja2Templates(directory=BASE_DIR / "templates", context_processors=[user_context])
templates.env.globals['asset_version'] = lambda path: (BASE_DIR / 'static' / path).stat().st_mtime_ns
