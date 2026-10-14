from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.auth import get_current_user, get_user_tier

BASE_DIR = Path(__file__).resolve().parent


def user_context(request: Request) -> dict:
    """Makes `current_user` and `user_tier` available in every template (the nav uses them)."""
    return {"current_user": get_current_user(request), "user_tier": get_user_tier(request)}


templates = Jinja2Templates(directory=BASE_DIR / "templates", context_processors=[user_context])
