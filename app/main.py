from datetime import date, timedelta
import urllib.parse
import os
import hmac
import hashlib

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth import admin_credentials_ok, is_admin_logged_in, require_admin
from app.db import (
    ensure_event_for_date,
    get_event,
    init_db,
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
    list_active_offers_for_date,
    create_reservation,
    set_reservation_lines,
    list_reservations_with_lines,
    reservation_exists_for_event,
    toggle_event_planned,
)

app = FastAPI(title="Breakfast Booking")

SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-change-me")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")  # ex: https://xxxxx.app.github.dev

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


LINK_SECRET = os.getenv("LINK_SECRET", SESSION_SECRET)  # secret dédié possible


def sign_agent_link(agent_id: int, event_date: str) -> str:
    msg = f"{agent_id}|{event_date}".encode("utf-8")
    return hmac.new(LINK_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def verify_agent_link(agent_id: int, event_date: str, token: str) -> bool:
    if not token:
        return False
    expected = sign_agent_link(agent_id, event_date)
    return hmac.compare_digest(expected, token)


def flash(request: Request, message: str, level: str = "success") -> None:
    request.session["flash"] = {"message": message, "level": level}


def pop_flash(request: Request):
    return request.session.pop("flash", None)


# =========================
# HOME
# =========================
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    event_date = tomorrow_str()
    tomorrow_date = date.today() + timedelta(days=1)

    # Garantir l'event de demain (menu auto)
    ensure_event_for_date(event_date, menu_for_date(tomorrow_date))

    event = get_event(event_date)
    if not event:
        return HTMLResponse("Event introuvable", status_code=500)

    # Offres actives pour demain
    offers = list_active_offers_for_date(event_date)
    mains = offers["mains"]
    sides = offers["sides"]
    no_offers = (len(mains) == 0 and len(sides) == 0)

    # Réservations (avec lignes)
    reservations = list_reservations_with_lines(event["id"])

    # Flash (1 seule fois)
    flash_data = pop_flash(request)

    # --- Prefill & lock name via signed link (agent_id + date) ---
    agent_q = request.query_params.get("agent")
    d_q = request.query_params.get("d")
    k_q = request.query_params.get("k")

    prefill_name = ""
    name_locked = False
    agent_id_for_form = ""
    d_for_form = ""
    k_for_form = ""

    if agent_q and d_q and k_q:
        try:
            aid = int(agent_q)
            if d_q == event_date and verify_agent_link(aid, d_q, k_q):
                agents_all = list_agents(active_only=False)
                agent = next((a for a in agents_all if a["id"] == aid), None)
                if agent:
                    prefill_name = agent["name"]
                    name_locked = True
                    agent_id_for_form = str(aid)
                    d_for_form = d_q
                    k_for_form = k_q
        except Exception:
            pass

    from_link = bool(name_locked)

    # Déjà réservé ? (uniquement si lien valide + nom fiable)
    already_reserved = False
    if from_link and prefill_name:
        already_reserved = reservation_exists_for_event(event["id"], prefill_name)

    # Message unique à afficher quand on ne peut pas réserver
    reserve_reason = None
    reserve_message = None

    # Priorités (du plus bloquant au moins bloquant)
    if not event.get("is_planned", True):
        reserve_reason = "not_planned"
        reserve_message = "Pas de petit-déjeuner prévu demain."
    elif not event["open"]:
        reserve_reason = "closed"
        reserve_message = "Réservations fermées."
    elif not from_link:
        reserve_reason = "secure"
        reserve_message = "Accès sécurisé requis : utilise le lien WhatsApp reçu."
    elif already_reserved:
        reserve_reason = "already"
        reserve_message = "Tu as déjà réservé pour demain 🙂"
    elif no_offers:
        reserve_reason = "no_offers"
        reserve_message = "Aucune offre n’est définie pour demain."

    can_reserve = (reserve_reason is None)

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "event": event,
            "reservations": reservations,
            "mains": mains,
            "sides": sides,
            "flash": flash_data,
            "prefill_name": prefill_name,
            "name_locked": name_locked,
            "agent_id": agent_id_for_form,
            "d": d_for_form,
            "k": k_for_form,
            "from_link": from_link,
            "can_reserve": can_reserve,
            "reserve_reason": reserve_reason,
            "reserve_message": reserve_message,
            "already_reserved": already_reserved,
            "no_offers": no_offers,
        },
    )


# =========================
# ADMIN: Toggle open/close
# =========================
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


# ✅ ADMIN: Toggle planned/unplanned (pas de petit dej demain)
@app.post("/admin/toggle-planned")
def admin_toggle_planned(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    event_date = tomorrow_str()
    tomorrow_date = date.today() + timedelta(days=1)

    ensure_event_for_date(event_date, menu_for_date(tomorrow_date))
    event = get_event(event_date)
    if event:
        toggle_event_planned(event["id"])

    return RedirectResponse("/", status_code=303)


# =========================
# ADMIN: Agents
# =========================
@app.get("/admin/agents", response_class=HTMLResponse)
def admin_agents(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    agents = list_agents()
    return templates.TemplateResponse("admin_agents.html", {"request": request, "agents": agents})


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
def admin_agents_delete(request: Request, agent_id: int = Form(...)):
    guard = require_admin(request)
    if guard:
        return guard

    # soft delete = désactiver
    set_agent_active(agent_id, False)
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


# =========================
# Helpers WhatsApp
# =========================
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


# =========================
# ADMIN: Shifts
# =========================
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

    if PUBLIC_BASE_URL:
        base_url = PUBLIC_BASE_URL + "/"
    else:
        base_url = str(request.base_url).rstrip("/") + "/"

    working_agents = list_working_agents_for_date(shift_date)

    wa_links = {}
    if event:
        menu_text = ", ".join(event["menu"])

        for a in working_agents:
            if not a["whatsapp_optin"]:
                continue

            token = sign_agent_link(a["id"], event["date"])
            personal_link = f"{base_url}?agent={a['id']}&d={event['date']}&k={token}"

            msg = (
                f"Salut 👋 Petit dej du {event['date']} : {menu_text}.\n"
                f"Réserve ici : {personal_link}\n"
                f"Si tu ramènes quelque chose, indique-le dans l’app 🙂"
            )

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


# =========================
# AUTH
# =========================
@app.get("/admin/login", response_class=HTMLResponse)
def admin_login(request: Request):
    if is_admin_logged_in(request):
        return RedirectResponse("/admin", status_code=303)

    return templates.TemplateResponse("admin_login.html", {"request": request, "error": None})


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

    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "flash": flash_data})


@app.get("/admin/week-menu", response_class=HTMLResponse)
def admin_week_menu(request: Request, week_start: str | None = None):
    guard = require_admin(request)
    if guard:
        return guard

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


# =========================
# ADMIN: Foods
# =========================
@app.get("/admin/foods", response_class=HTMLResponse)
def admin_foods(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    foods = list_foods(active_only=False)
    return templates.TemplateResponse("admin_foods.html", {"request": request, "foods": foods})


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


# =========================
# ADMIN: Recipes
# =========================
@app.get("/admin/recipes", response_class=HTMLResponse)
def admin_recipes(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    recipes = list_recipes(active_only=False)
    return templates.TemplateResponse("admin_recipes.html", {"request": request, "recipes": recipes})


@app.post("/admin/recipes/add")
def admin_recipes_add(request: Request, name: str = Form(...)):
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


# =========================
# ADMIN: Offers
# =========================
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


# =========================
# RESERVE (ultra safe)
# =========================
@app.post("/reserve")
async def reserve(request: Request):
    form = await request.form()

    bring = (form.get("bring") or "").strip()

    event_date = tomorrow_str()
    tomorrow_date = date.today() + timedelta(days=1)

    # Toujours garantir event existant
    ensure_event_for_date(event_date, menu_for_date(tomorrow_date))
    event = get_event(event_date)

    # Planned + open obligatoires
    if (not event) or (not event.get("is_planned", True)) or (not event["open"]):
        flash(request, "Réservations fermées (ou aucun petit-déjeuner prévu).", "error")
        return RedirectResponse("/", status_code=303)

    # --- ULTRA SAFE : on exige un lien signé ---
    agent_q = (form.get("agent") or "").strip()
    d_q = (form.get("d") or "").strip()
    k_q = (form.get("k") or "").strip()

    if not (agent_q and d_q and k_q):
        flash(request, "Accès sécurisé requis : utilise ton lien WhatsApp.", "error")
        return RedirectResponse("/", status_code=303)

    try:
        aid = int(agent_q)
    except Exception:
        flash(request, "Lien invalide.", "error")
        return RedirectResponse("/", status_code=303)

    # La date du lien doit matcher l'event du jour (demain)
    if d_q != event_date or not verify_agent_link(aid, d_q, k_q):
        flash(request, "Lien expiré ou invalide.", "error")
        return RedirectResponse("/", status_code=303)

    # Bonus sécurité : l'agent doit faire partie des agents “de demain”
    working_ids = list_working_agent_ids(event_date)
    if aid not in set(working_ids):
        flash(request, "Lien non autorisé pour cet événement.", "error")
        return RedirectResponse("/", status_code=303)

    # On force le nom depuis la DB
    agents_all = list_agents(active_only=False)
    agent = next((a for a in agents_all if a["id"] == aid), None)
    if not agent:
        flash(request, "Agent introuvable.", "error")
        return RedirectResponse("/", status_code=303)

    name = agent["name"]

    # Anti double réservation
    if reservation_exists_for_event(event["id"], name):
        flash(request, "Tu as déjà réservé pour demain 🙂", "warning")
        return RedirectResponse(f"/?agent={aid}&d={event_date}&k={k_q}", status_code=303)

    # --- Validation des offers côté serveur ---
    offers_list = list_offers_for_date(event_date)
    if not offers_list:
        flash(request, "Aucune offre n’est définie pour demain.", "error")
        return RedirectResponse(f"/?agent={aid}&d={event_date}&k={k_q}", status_code=303)

    offers_by_id = {o["id"]: o for o in offers_list}
    lines: list[tuple[int, int]] = []

    # 1) MAIN : choix unique (radio)
    main_choice = form.get("main_choice")
    if main_choice:
        try:
            main_offer_id = int(main_choice)
        except Exception:
            flash(request, "Choix invalide.", "error")
            return RedirectResponse(f"/?agent={aid}&d={event_date}&k={k_q}", status_code=303)

        o = offers_by_id.get(main_offer_id)
        if not o or o.get("offer_type") != "MAIN" or not o.get("is_active"):
            flash(request, "Plat invalide.", "error")
            return RedirectResponse(f"/?agent={aid}&d={event_date}&k={k_q}", status_code=303)

        qty_key = f"main_qty_{main_offer_id}"
        try:
            main_qty = int(form.get(qty_key) or 1)
        except Exception:
            main_qty = 1

        max_pp = int(o.get("max_per_person") or 1)
        if main_qty < 1:
            main_qty = 1
        if main_qty > max_pp:
            main_qty = max_pp

        lines.append((main_offer_id, main_qty))

    # 2) SIDE : quantités multiples offer_<id>
    for key, val in form.items():
        if not key.startswith("offer_"):
            continue
        try:
            offer_id = int(key.split("_", 1)[1])
            qty = int(val)
        except Exception:
            continue

        if qty <= 0:
            continue

        o = offers_by_id.get(offer_id)
        if not o or o.get("offer_type") != "SIDE" or not o.get("is_active"):
            continue

        max_pp = int(o.get("max_per_person") or 1)
        if qty > max_pp:
            qty = max_pp

        lines.append((offer_id, qty))

    # Bonus : refuser > 1 MAIN (requête forgée)
    main_count = sum(
        1
        for offer_id, qty in lines
        if qty > 0 and offers_by_id.get(offer_id) and offers_by_id[offer_id].get("offer_type") == "MAIN"
    )
    if main_count > 1:
        flash(request, "Choix invalide (un seul plat).", "error")
        return RedirectResponse(f"/?agent={aid}&d={event_date}&k={k_q}", status_code=303)

    # Validation : au moins 1 choix ou bring
    if not lines and not bring:
        flash(request, "Choisis au moins un plat / accompagnement, ou indique ce que tu ramènes.", "warning")
        return RedirectResponse(f"/?agent={aid}&d={event_date}&k={k_q}", status_code=303)

    # Persist
    reservation_id = create_reservation(event["id"], name, bring)
    if lines:
        set_reservation_lines(reservation_id, lines)

    flash(request, "✅ Réservation enregistrée !", "success")
    return RedirectResponse(f"/?agent={aid}&d={event_date}&k={k_q}", status_code=303)
