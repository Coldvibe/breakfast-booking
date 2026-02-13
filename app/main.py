"""
app/main.py

Point d’entrée de l’app FastAPI.
Ici je garde uniquement:
- config FastAPI
- middleware sessions (admin + flash)
- templates + static
- helpers partagés via app.state (pour éviter les imports circulaires)
- include_router(public + admin)
"""

from datetime import date, timedelta
import os
import hmac
import hashlib

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.db import init_db, get_weekly_menu
from app.routers.public import router as public_router
from app.routers.admin import router as admin_router


# -------------------------
# App / config
# -------------------------
app = FastAPI(title="Breakfast Booking")

SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-change-me")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")  # ex: https://xxxxx.app.github.dev
LINK_SECRET = os.getenv("LINK_SECRET", SESSION_SECRET)  # secret dédié pour signer les liens (fallback sur session)


# Sessions (cookie signé) : utilisé pour l'admin + flash messages
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=True,  # Codespaces est en HTTPS => on force un cookie HTTPS only
)

# Templates Jinja
templates = Jinja2Templates(directory="app/templates")

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# -------------------------
# Constantes menus
# -------------------------
DEFAULT_MENU = ["Œufs", "Pain", "Charcuterie", "Pancakes"]
DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


# -------------------------
# Helpers dates / menus
# -------------------------
def monday_of_week(d: date) -> date:
    # Monday = 0
    return d - timedelta(days=d.weekday())


def menu_for_date(d: date) -> list[str]:
    # Récupère le menu de la semaine (weekly_menus), sinon fallback sur DEFAULT_MENU
    week_start = monday_of_week(d).isoformat()
    data = get_weekly_menu(week_start)
    if not data:
        return DEFAULT_MENU

    day_key = DAYS[d.weekday()]
    items = data["menu"].get(day_key, [])
    return items if items else DEFAULT_MENU


def tomorrow_str() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


# -------------------------
# Helpers liens signés (WhatsApp)
# -------------------------
def sign_agent_link(agent_id: int, event_date: str) -> str:
    # token = HMAC(secret, "agent_id|YYYY-MM-DD")
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
    # Stocké en session et consommé à l’affichage suivant
    request.session["flash"] = {"message": message, "level": level}


def pop_flash(request: Request):
    return request.session.pop("flash", None)


# -------------------------
# app.state (partagé aux routers)
# IMPORTANT: on le fait APRES la définition des fonctions
# -------------------------
# Les routers peuvent récupérer:
#   request.app.state.flash(...)
#   request.app.state.templates.TemplateResponse(...)
app.state.templates = templates
app.state.flash = flash
app.state.pop_flash = pop_flash

app.state.tomorrow_str = tomorrow_str
app.state.menu_for_date = menu_for_date

app.state.sign_agent_link = sign_agent_link
app.state.verify_agent_link = verify_agent_link

# utile pour générer les liens WhatsApp côté admin
app.state.public_base_url = PUBLIC_BASE_URL


# -------------------------
# Routers
# -------------------------
# Public: "/" + "/reserve"
app.include_router(public_router)

# Admin: "/admin/..."
app.include_router(admin_router)


# -------------------------
# Startup
# -------------------------
@app.on_event("startup")
def on_startup():
    # Safe: CREATE TABLE IF NOT EXISTS + migrations légères si on en ajoute
    init_db()
