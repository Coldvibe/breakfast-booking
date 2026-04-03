"""
app/main.py

Point d’entrée de l’app FastAPI.
Ici je garde uniquement:
- config FastAPI
- middleware sessions (admin + flash)
- templates + static
- helpers partagés via app.state (pour éviter les imports circulaires)
- include_router(public + admin)
- service du frontend React buildé
"""

from datetime import date, timedelta
from pathlib import Path
import hashlib
import hmac
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.db import init_db
from app.routers.admin import router as admin_router
from app.routers.public import router as public_router


# -------------------------
# App / config
# -------------------------
app = FastAPI(title="Breakfast Booking")

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
FRONTEND_ASSETS = FRONTEND_DIST / "assets"

SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-change-me")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
LINK_SECRET = os.getenv("LINK_SECRET", SESSION_SECRET)


# -------------------------
# Middleware
# -------------------------
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=True,
)


# -------------------------
# Templates / static
# -------------------------
templates = Jinja2Templates(directory="app/templates")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

if FRONTEND_ASSETS.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_ASSETS)), name="frontend-assets")


# -------------------------
# Constantes menus
# -------------------------
DEFAULT_MENU = ["Œufs", "Pain", "Charcuterie", "Pancakes"]
DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


# -------------------------
# Helpers dates / menus
# -------------------------
def monday_of_week(d: date) -> date:
    return d - timedelta(days=d.weekday())


def menu_for_date(d: date) -> list[str]:
    return DEFAULT_MENU


def tomorrow_str() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


# -------------------------
# Helpers liens signés (WhatsApp)
# -------------------------
def sign_agent_link(agent_id: int, event_date: str) -> str:
    msg = f"{agent_id}|{event_date}".encode("utf-8")
    return hmac.new(LINK_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def verify_agent_link(agent_id: int, event_date: str, token: str) -> bool:
    if not token:
        return False
    expected = sign_agent_link(agent_id, event_date)
    return hmac.compare_digest(expected, token)


# -------------------------
# Helpers flash messages
# -------------------------
def flash(request: Request, message: str, level: str = "success") -> None:
    request.session["flash"] = {"message": message, "level": level}


def pop_flash(request: Request):
    return request.session.pop("flash", None)


# -------------------------
# app.state
# -------------------------
app.state.templates = templates
app.state.flash = flash
app.state.pop_flash = pop_flash
app.state.tomorrow_str = tomorrow_str
app.state.menu_for_date = menu_for_date
app.state.sign_agent_link = sign_agent_link
app.state.verify_agent_link = verify_agent_link
app.state.public_base_url = PUBLIC_BASE_URL


# -------------------------
# Routers
# -------------------------
app.include_router(public_router)
app.include_router(admin_router)


# -------------------------
# Frontend React buildé
# -------------------------
@app.get("/{full_path:path}")
def frontend_app(full_path: str):
    # Ne jamais laisser le frontend avaler les routes API
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")

    # Fichiers réels dans dist (manifest, icônes, etc.)
    target_file = FRONTEND_DIST / full_path
    if full_path and target_file.exists() and target_file.is_file():
        return FileResponse(target_file)

    # SPA fallback
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    raise HTTPException(status_code=500, detail="Frontend not built")


# -------------------------
# Startup
# -------------------------
@app.on_event("startup")
def on_startup():
    init_db()