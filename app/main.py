from datetime import date, timedelta, datetime
import urllib.parse
import os

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.auth import admin_credentials_ok, is_admin_logged_in, require_admin
from fastapi.staticfiles import StaticFiles
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
    get_weekly_menu,
    upsert_weekly_menu,
    upsert_event_menu_preserve_open,
    update_agent,
    list_foods,
    add_food,
    set_food_active,
    list_recipes,
    add_recipe,
    set_recipe_active,
    list_offers_for_date,
    add_offer_main,
    add_offer_side,
    update_offer_max,
    set_offer_active,




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
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# safe: garantit DB + tables
init_db()

DEFAULT_MENU = ["Œufs", "Pain", "Charcuterie", "Pancakes"]


def monday_of_week(d: date) -> date:
    return d - timedelta(days=d.weekday())  # Monday = 0


DAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def menu_for_date(d: date) -> list[str]:
    week_start = monday_of_week(d).isoformat()
    data = get_weekly_menu(week_start)
    if not data:
        return DEFAULT_MENU

    day_key = DAYS[d.weekday()]  # 0=lundi ...
    items = data["menu"].get(day_key, [])
    return items if items else DEFAULT_MENU


@app.on_event("startup")
def on_startup():
    init_db()


def tomorrow_str() -> str:
    return (date.today() + timedelta(days=1)).isoformat()
def flash(request: Request, message: str, level: str = "success") -> None:
    request.session["flash"] = {"message": message, "level": level}


def pop_flash(request: Request):
    return request.session.pop("flash", None)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    event_date = tomorrow_str()
    tomorrow_date = date.today() + timedelta(days=1)

    ensure_event_for_date(event_date, menu_for_date(tomorrow_date))

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
    tomorrow_date = date.today() + timedelta(days=1)

    ensure_event_for_date(event_date, menu_for_date(tomorrow_date))
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
    tomorrow_date = date.today() + timedelta(days=1)

    ensure_event_for_date(event_date, menu_for_date(tomorrow_date))
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
    tomorrow_date = date.today() + timedelta(days=1)

    ensure_event_for_date(event_date, menu_for_date(tomorrow_date))
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

    flash_data = pop_flash(request)

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {"request": request, "flash": flash_data},
    )

@app.get("/admin/week-menu", response_class=HTMLResponse)
def admin_week_menu(request: Request, week_start: str | None = None):
    guard = require_admin(request)
    if guard:
        return guard

    # semaine courante par défaut
    if not week_start:
        week_start_date = monday_of_week(date.today())
        week_start = week_start_date.isoformat()

    data = get_weekly_menu(week_start)
    menu = data["menu"] if data else {d: [] for d in DAYS}

    return templates.TemplateResponse(
        "admin_week_menu.html",
        {"request": request, "week_start": week_start, "menu": menu, "days": DAYS},
    )

@app.post("/admin/sync-tomorrow")
def admin_sync_tomorrow(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    event_date = tomorrow_str()
    tomorrow_date = date.today() + timedelta(days=1)

    upsert_event_menu_preserve_open(event_date, menu_for_date(tomorrow_date))

    flash(request, "✅ Menu de demain synchronisé avec le menu de la semaine.")
    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/week-menu/save")
def admin_week_menu_save(
    request: Request,
    week_start: str = Form(...),
    lundi: str = Form(""),
    mardi: str = Form(""),
    mercredi: str = Form(""),
    jeudi: str = Form(""),
    vendredi: str = Form(""),
    samedi: str = Form(""),
    dimanche: str = Form(""),
):
    guard = require_admin(request)
    if guard:
        return guard

    def parse_items(s: str) -> list[str]:
        return [x.strip() for x in s.split(",") if x.strip()]

    menu = {
        "lundi": parse_items(lundi),
        "mardi": parse_items(mardi),
        "mercredi": parse_items(mercredi),
        "jeudi": parse_items(jeudi),
        "vendredi": parse_items(vendredi),
        "samedi": parse_items(samedi),
        "dimanche": parse_items(dimanche),
    }

    upsert_weekly_menu(week_start, menu)
    return RedirectResponse(f"/admin/week-menu?week_start={week_start}", status_code=303)
@app.post("/admin/agents/update")
def admin_agents_update(
    request: Request,
    agent_id: int = Form(...),
    name: str = Form(...),
    phone: str = Form(...),
    whatsapp_optin: bool = Form(False),
    is_active: bool = Form(False),
):
    guard = require_admin(request)
    if guard:
        return guard

    update_agent(agent_id, name, phone, whatsapp_optin, is_active)
    return RedirectResponse("/admin/agents", status_code=303)


@app.post("/admin/agents/delete")
def admin_agents_delete(
    request: Request,
    agent_id: int = Form(...),
):
    guard = require_admin(request)
    if guard:
        return guard

    # soft delete = désactiver
    set_agent_active(agent_id, False)
    return RedirectResponse("/admin/agents", status_code=303)
@app.get("/admin/go")
def admin_go(request: Request):
    if is_admin_logged_in(request):
        return RedirectResponse("/admin", status_code=303)
    return RedirectResponse("/admin/login", status_code=303)
@app.get("/admin/foods", response_class=HTMLResponse)
def admin_foods(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    foods = list_foods(active_only=False)
    return templates.TemplateResponse(
        "admin_foods.html",
        {"request": request, "foods": foods},
    )


@app.post("/admin/foods/add")
def admin_foods_add(
    request: Request,
    name: str = Form(...),
    unit: str = Form("unit"),
):
    guard = require_admin(request)
    if guard:
        return guard

    add_food(name=name, unit=unit)
    return RedirectResponse("/admin/foods", status_code=303)


@app.post("/admin/foods/toggle")
def admin_foods_toggle(
    request: Request,
    food_id: int = Form(...),
    is_active: int = Form(...),
):
    guard = require_admin(request)
    if guard:
        return guard

    set_food_active(food_id, bool(is_active))
    return RedirectResponse("/admin/foods", status_code=303)
@app.get("/admin/recipes", response_class=HTMLResponse)
def admin_recipes(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    recipes = list_recipes(active_only=False)
    return templates.TemplateResponse(
        "admin_recipes.html",
        {"request": request, "recipes": recipes},
    )


@app.post("/admin/recipes/add")
def admin_recipes_add(
    request: Request,
    name: str = Form(...),
):
    guard = require_admin(request)
    if guard:
        return guard

    add_recipe(name=name)
    return RedirectResponse("/admin/recipes", status_code=303)


@app.post("/admin/recipes/toggle")
def admin_recipes_toggle(
    request: Request,
    recipe_id: int = Form(...),
    is_active: int = Form(...),
):
    guard = require_admin(request)
    if guard:
        return guard

    set_recipe_active(recipe_id, bool(is_active))
    return RedirectResponse("/admin/recipes", status_code=303)
@app.get("/admin/offers", response_class=HTMLResponse)
def admin_offers(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    offer_date = tomorrow_str()

    recipes = list_recipes(active_only=True)
    foods = list_foods(active_only=True)
    offers = list_offers_for_date(offer_date)

    mains = [o for o in offers if o["offer_type"] == "MAIN"]
    sides = [o for o in offers if o["offer_type"] == "SIDE"]

    return templates.TemplateResponse(
        "admin_offers.html",
        {
            "request": request,
            "offer_date": offer_date,
            "recipes": recipes,
            "foods": foods,
            "mains": mains,
            "sides": sides,
        },
    )


@app.post("/admin/offers/add-main")
def admin_offers_add_main(
    request: Request,
    recipe_id: int = Form(...),
    max_per_person: int = Form(1),
):
    guard = require_admin(request)
    if guard:
        return guard

    add_offer_main(tomorrow_str(), recipe_id, max_per_person)
    return RedirectResponse("/admin/offers", status_code=303)


@app.post("/admin/offers/add-side")
def admin_offers_add_side(
    request: Request,
    food_id: int = Form(...),
    max_per_person: int = Form(1),
):
    guard = require_admin(request)
    if guard:
        return guard

    add_offer_side(tomorrow_str(), food_id, max_per_person)
    return RedirectResponse("/admin/offers", status_code=303)


@app.post("/admin/offers/update-max")
def admin_offers_update_max(
    request: Request,
    offer_id: int = Form(...),
    max_per_person: int = Form(...),
):
    guard = require_admin(request)
    if guard:
        return guard

    update_offer_max(offer_id, max_per_person)
    return RedirectResponse("/admin/offers", status_code=303)


@app.post("/admin/offers/toggle")
def admin_offers_toggle(
    request: Request,
    offer_id: int = Form(...),
    is_active: int = Form(...),
):
    guard = require_admin(request)
    if guard:
        return guard

    set_offer_active(offer_id, bool(is_active))
    return RedirectResponse("/admin/offers", status_code=303)
