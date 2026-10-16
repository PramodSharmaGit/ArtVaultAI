"""Public information pages linked from the footer."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.models import FREE_DOWNLOAD_CAP
from app.templating import templates

router = APIRouter()


@router.get('/how-it-works', response_class=HTMLResponse)
def how_it_works(request: Request):
    return templates.TemplateResponse(request, 'information.html', {'page': 'how', 'download_cap': FREE_DOWNLOAD_CAP})


@router.get('/membership', response_class=HTMLResponse)
def membership(request: Request):
    return templates.TemplateResponse(request, 'information.html', {'page': 'membership', 'download_cap': FREE_DOWNLOAD_CAP})


@router.get('/contact', response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse(request, 'information.html', {'page': 'contact'})


@router.get('/community', response_class=HTMLResponse)
def community(request: Request):
    return templates.TemplateResponse(request, 'information.html', {'page': 'community'})


@router.get('/privacy', response_class=HTMLResponse)
def privacy(request: Request):
    return templates.TemplateResponse(request, 'information.html', {'page': 'privacy'})


@router.get('/terms', response_class=HTMLResponse)
def terms(request: Request):
    return templates.TemplateResponse(request, 'information.html', {'page': 'terms'})


@router.get('/about', response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse(request, 'information.html', {'page': 'about'})


@router.get('/faq', response_class=HTMLResponse)
def faq(request: Request):
    return templates.TemplateResponse(request, 'information.html', {'page': 'faq', 'download_cap': FREE_DOWNLOAD_CAP})


@router.get('/activity-safety', response_class=HTMLResponse)
def activity_safety(request: Request):
    return templates.TemplateResponse(request, 'information.html', {'page': 'safety'})
