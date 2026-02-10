from datetime import date, timedelta
import urllib.parse
import os

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.auth import admin_credentials_ok, is_admin_logged_in, require_admin

from app.db import (
    add_reservation,
    ensure_event_for_date,
    get_event,
    init_db,
    list_reservations,
    toggle_event_open,
    list_agents,
    add_agent,
    set_agent_active,
    set_agent_whatsapp_optin,
    list_working_agent_ids,
    set_working_agents_for_date,
    list_working_agents_for_date,
)

app = FastAPI(title="Breakfast Booking")

SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-change-me")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=True,  # cookies uniquement en HTTPS (Codespaces est HTTPS)
)

templates = Jinja2Templates(directory="app/templates")

# safe: garantit DB + tables
init_db()

DEFAULT_MENU = ["Œufs", "Pain", "Charcuterie", "Pancakes"]


@app.on_event("startup")
def on_startup():
    init_db()


def tomorrow_str() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    event_date = tomorrow_str()
    ensure_event_for_date(event_date, DEFAULT_MENU)

    event = get_event(event_date)
    if not event:
        return HTMLResponse("Event introuvable", status_code=500)

    reservations = list_reservations(event["id"])

    return templates.TemplateResponse(
        "home.html",
        {"request": request, "event": event, "reservations": reservations},
    )


@app.post("/reserve")
def reserve(
    name: str = Form(...),
    items: str = Form(""),
    bring: str = Form(""),
):
    event_date = tomorrow_str()
    ensure_event_for_date(event_date, DEFAULT_MENU)
    event = get_event(event_date)
    if not event:
        return RedirectResponse("/", status_code=303)

    if not event["open"]:
        return RedirectResponse("/", status_code=303)

    clean_name = name.strip()
    clean_items = [i.strip() for i in items.split(",") if i.strip()]
    clean_bring = bring.strip()

    if clean_name:
        add_reservation(event["id"], clean_name, clean_items, clean_bring)

    return RedirectResponse("/", status_code=303)


# ✅ ADMIN (protégé)
@app.post("/admin/toggle")
def admin_toggle(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    event_date = tomorrow_str()
    ensure_event_for_date(event_date, DEFAULT_MENU)
    event = get_event(event_date)
    if event:
        toggle_event_open(event["id"])
    return RedirectResponse("/", status_code=303)


# ✅ ADMIN AGENTS (protégé)
@app.get("/admin/agents", response_class=HTMLResponse)
def admin_agents(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    agents = list_agents()
    return templates.TemplateResponse(
        "admin_agents.html",
        {"request": request, "agents": agents},
    )


@app.post("/admin/agents/add")
def admin_agents_add(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    whatsapp_optin: bool = Form(False),
):
    guard = require_admin(request)
    if guard:
        return guard

    add_agent(name=name, phone=phone, whatsapp_optin=whatsapp_optin)
    return RedirectResponse("/admin/agents", status_code=303)


@app.post("/admin/agents/toggle-active")
def admin_agents_toggle_active(
    request: Request,
    agent_id: int = Form(...),
    is_active: int = Form(...),
):
    guard = require_admin(request)
    if guard:
        return guard

    set_agent_active(agent_id, bool(is_active))
    return RedirectResponse("/admin/agents", status_code=303)


@app.post("/admin/agents/toggle-whatsapp")
def admin_agents_toggle_whatsapp(
    request: Request,
    agent_id: int = Form(...),
    whatsapp_optin: int = Form(...),
):
    guard = require_admin(request)
    if guard:
        return guard

    set_agent_whatsapp_optin(agent_id, bool(whatsapp_optin))
    return RedirectResponse("/admin/agents", status_code=303)


# Helpers WhatsApp
def normalize_phone_to_e164(phone: str) -> str:
    p = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if p.startswith("00"):
        p = "+" + p[2:]
    return p


def wa_me_link(phone: str, message: str) -> str:
    p = normalize_phone_to_e164(phone)
    p_digits = p.replace("+", "")
    text = urllib.parse.quote(message)
    return f"https://wa.me/{p_digits}?text={text}"


# ✅ ADMIN SHIFTS (protégé)
@app.get("/admin/shifts", response_class=HTMLResponse)
def admin_shifts(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    shift_date = tomorrow_str()

    agents = list_agents(active_only=True)
    working_ids = list_working_agent_ids(shift_date)

    # menu de demain + lien de réservation
    event_date = tomorrow_str()
    ensure_event_for_date(event_date, DEFAULT_MENU)
    event = get_event(event_date)

    reservations_url = str(request.base_url).rstrip("/") + "/"
    working_agents = list_working_agents_for_date(shift_date)

    wa_links = {}
    if event:
        menu_text = ", ".join(event["menu"])
        msg = (
            f"Salut 👋 Petit dej du {event['date']} : {menu_text}.\n"
            f"Réserve ici : {reservations_url}\n"
            f"Si tu ramènes quelque chose, indique-le dans l’app 🙂"
        )
        for a in working_agents:
            if a["whatsapp_optin"]:
                wa_links[a["id"]] = wa_me_link(a["phone"], msg)

    return templates.TemplateResponse(
        "admin_shifts.html",
        {
            "request": request,
            "shift_date": shift_date,
            "agents": agents,
            "working_ids": working_ids,
            "working_agents": working_agents,
            "wa_links": wa_links,
        },
    )


@app.post("/admin/shifts/save")
def admin_shifts_save(
    request: Request,
    shift_date: str = Form(...),
    working_agent_ids: list[int] = Form(default=[]),
):
    guard = require_admin(request)
    if guard:
        return guard

    set_working_agents_for_date(shift_date, working_agent_ids)
    return RedirectResponse("/admin/shifts", status_code=303)


# ✅ AUTH
@app.get("/admin/login", response_class=HTMLResponse)
def admin_login(request: Request):
    if is_admin_logged_in(request):
        return RedirectResponse("/admin", status_code=303)

    return templates.TemplateResponse(
        "admin_login.html",
        {"request": request, "error": None},
    )


@app.post("/admin/login")
def admin_login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if admin_credentials_ok(username.strip(), password):
        request.session["admin"] = True
        return RedirectResponse("/admin", status_code=303)

    return templates.TemplateResponse(
        "admin_login.html",
        {"request": request, "error": "Identifiants incorrects"},
        status_code=401,
    )


@app.post("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {"request": request},
    )
