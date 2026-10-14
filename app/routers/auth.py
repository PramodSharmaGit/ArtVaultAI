import uuid

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from supabase import AuthError

from app.auth import (clear_session_cookies, ensure_profile, get_current_user, set_session_cookies,
                      supabase_client)
from app.db import get_db
from app.templating import templates

router = APIRouter()

MIN_PASSWORD = 8


def friendly_error(exc: AuthError) -> str:
    msg = (getattr(exc, "message", "") or str(exc)).lower()
    if "already registered" in msg or "already exists" in msg:
        return "An account with this email already exists. Try logging in."
    if "invalid login" in msg or "invalid credentials" in msg:
        return "Incorrect email or password."
    if "not confirmed" in msg:
        return "Please confirm your email first, then log in."
    if "password" in msg:
        return f"Please choose a stronger password (at least {MIN_PASSWORD} characters)."
    if "rate limit" in msg or "too many" in msg:
        return "Too many attempts. Please wait a moment and try again."
    return "Something went wrong. Please try again."


def render(request: Request, template: str, status_code: int = 200, **context) -> HTMLResponse:
    return templates.TemplateResponse(request, template, context, status_code=status_code)


def logged_in_redirect(request: Request, session) -> RedirectResponse:
    response = RedirectResponse("/", status_code=303)
    set_session_cookies(response, session, secure=request.url.scheme == "https")
    return response


@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    if get_current_user(request):
        return RedirectResponse("/", status_code=303)
    return render(request, "signup.html")


@router.post("/signup", response_class=HTMLResponse)
def signup_submit(request: Request, name: str = Form(""), email: str = Form(""), password: str = Form(""),
                  db: Session = Depends(get_db)):
    name = " ".join(name.split())[:60]
    email = email.strip().lower()
    if not name or "@" not in email or len(password) < MIN_PASSWORD:
        return render(request, "signup.html", 400, name=name, email=email,
                      error=f"Enter your name, a valid email and a password of at least {MIN_PASSWORD} characters.")
    try:
        result = supabase_client().auth.sign_up(
            {"email": email, "password": password, "options": {"data": {"full_name": name}}})
    except AuthError as exc:
        return render(request, "signup.html", 400, name=name, email=email, error=friendly_error(exc))
    if result.user is None:
        return render(request, "signup.html", 400, name=name, email=email, error="Something went wrong. Please try again.")

    ensure_profile(db, uuid.UUID(result.user.id))
    if result.session is None:  # Supabase is set to require email confirmation
        return render(request, "login.html", email=email,
                      notice="Almost there! Check your email to confirm your account, then log in.")
    return logged_in_redirect(request, result.session)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if get_current_user(request):
        return RedirectResponse("/", status_code=303)
    return render(request, "login.html")


@router.post("/login", response_class=HTMLResponse)
def login_submit(request: Request, email: str = Form(""), password: str = Form(""),
                 db: Session = Depends(get_db)):
    email = email.strip().lower()
    try:
        result = supabase_client().auth.sign_in_with_password({"email": email, "password": password})
    except AuthError as exc:
        return render(request, "login.html", 400, email=email, error=friendly_error(exc))
    if result.user is None or result.session is None:
        return render(request, "login.html", 400, email=email, error="Something went wrong. Please try again.")

    ensure_profile(db, uuid.UUID(result.user.id))
    return logged_in_redirect(request, result.session)


@router.post("/logout")
def logout():
    response = RedirectResponse("/", status_code=303)
    clear_session_cookies(response)
    return response
