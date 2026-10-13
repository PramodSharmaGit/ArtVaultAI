from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="The Art Vault")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Demo seed data (see AGENTS.md "Decided"). Replaced by DB query once the catalog exists.
PREVIEW_ASSETS = [
    {"title": "Window Garden Collage", "ages": "2–5", "materials": "Tissue paper & glue", "tier": "free", "image": "images/window-garden.jpeg", "image_alt": "Children creating a colorful tissue paper garden collage on a sunny window"},
    {"title": "Cloud Watching Journal", "ages": "5–9", "materials": "Printable journal", "tier": "free", "image": "images/cloud-journal.jpeg", "image_alt": "Children decorating cloud watching journals at a table beside sunny windows"},
    {"title": "Paper Rocket Kit", "ages": "6–10", "materials": "Cut & fold template", "tier": "member", "image": "images/paper-rocket.jpeg", "image_alt": "Children cutting and folding colorful paper rockets at a craft table"},
    {"title": "Sunshine Suncatcher", "ages": "3–8", "materials": "Tissue paper & contact film", "tier": "member", "image": "images/suncatcher.jpeg", "image_alt": "Children making sun-shaped suncatchers with colorful tissue paper and contact film"},
    {"title": "Pressed Flower Cards", "ages": "6–12", "materials": "Pressed flowers & cardstock", "tier": "member", "image": "images/pressed-flowers.jpeg", "image_alt": "Children arranging pressed flowers and leaves on cardstock to make greeting cards"},
    {"title": "Squiggle Monster Maker", "ages": "4–9", "materials": "Markers & cut-outs", "tier": "member", "image": "images/squiggle-monster.jpeg", "image_alt": "Children decorating colorful paper monsters with markers and cut-outs at a classroom craft table"},
]


@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return templates.TemplateResponse(request, "landing.html", {"assets": PREVIEW_ASSETS})
