# app/routers/admin.py

from __future__ import annotations

from datetime import date, timedelta
import urllib.parse
from typing import Optional

from fastapi import APIRouter, Form, Request,  HTTPException, Request, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

# + importe get_recipe, update_recipe
from hashlib import sha256
from app.auth import admin_credentials_ok, is_admin_logged_in, require_admin
from app.db import (
    get_conn,
    # events
    ensure_event_for_date,
    get_event,
    toggle_event_open,
    toggle_event_planned,
    get_tomorrow_admin_snapshot,
    update_event_flags,
    set_event_planned,
    set_event_breakfast_price,
    # agents
    list_agents,
    add_agent,
    update_agent,
    set_agent_active,
    set_agent_whatsapp_optin,
    set_working_agents_for_date,
    # shifts
    list_working_agent_ids,
    set_working_agents_for_date,
    list_working_agents_for_date,
    # foods
    list_foods,
    add_food,
    set_food_active,
    # recipes
    list_recipes,
    add_recipe,
    set_recipe_active,
    get_recipe,
    update_recipe,

    # offers
    list_offers_for_date,
    add_offer_main,
    add_offer_side,
    update_offer_max,
    set_offer_active,
    delete_offer,

    #user
    list_users,
    add_user,
    set_user_active,
    delete_user,
    update_user,
    authenticate_user,
    create_reservation,
    set_reservation_lines,
    delete_reservation_for_event_and_name,
    list_active_offers_for_date,
    list_reservations_with_lines,
    
)

router = APIRouter()


# -------------------------
# Helpers (petits utils)
# -------------------------

def _tomorrow_str() -> str:
    # On centralise le "demain" pour éviter de répéter partout
    return (date.today() + timedelta(days=1)).isoformat()

def _hash_password(password: str) -> str:
    return sha256(password.encode("utf-8")).hexdigest()

def _menu_for_tomorrow(request: Request) -> list[str]:
    # menu_for_date est stocké dans app.state (défini dans main.py)
    tomorrow_date = date.today() + timedelta(days=1)
    return request.app.state.menu_for_date(tomorrow_date)


def _flash(request: Request, message: str, level: str = "success") -> None:
    # flash() est stocké dans app.state (défini dans main.py)
    request.app.state.flash(request, message, level)


def _templates(request: Request):
    # templates est stocké dans app.state (défini dans main.py)
    return request.app.state.templates


def _base_url(request: Request) -> str:
    # Base URL de l’app (utile pour les liens WhatsApp)
    public_base = getattr(request.app.state, "public_base_url", "") or ""
    public_base = public_base.rstrip("/")
    if public_base:
        return public_base + "/"
    return str(request.base_url).rstrip("/") + "/"


def _normalize_phone_to_e164(phone: str) -> str:
    p = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if p.startswith("00"):
        p = "+" + p[2:]
    return p


def _wa_me_link(phone: str, message: str) -> str:
    p = _normalize_phone_to_e164(phone)
    p_digits = p.replace("+", "")
    text = urllib.parse.quote(message)
    return f"https://wa.me/{p_digits}?text={text}"


# -------------------------
# Admin "go" (raccourci)
# -------------------------

@router.get("/admin/go")
def admin_go(request: Request):
    # Petit raccourci: si déjà loggué => dashboard, sinon => login
    if is_admin_logged_in(request):
        return RedirectResponse("/admin", status_code=303)
    return RedirectResponse("/admin/login", status_code=303)


# -------------------------
# Auth admin
# -------------------------

@router.get("/admin/login", response_class=HTMLResponse)
def admin_login(request: Request):
    if is_admin_logged_in(request):
        return RedirectResponse("/admin", status_code=303)

    return _templates(request).TemplateResponse(
        "admin_login.html",
        {"request": request, "error": None},
    )


@router.post("/admin/login")
def admin_login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if admin_credentials_ok(username.strip(), password):
        request.session["admin"] = True
        return RedirectResponse("/admin", status_code=303)

    return _templates(request).TemplateResponse(
        "admin_login.html",
        {"request": request, "error": "Identifiants incorrects"},
        status_code=401,
    )


@router.get("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin/login", status_code=303)

# -------------------------
# Dashboard admin
# -------------------------

@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    # Protection admin
    guard = require_admin(request)
    if guard:
        return guard

    return RedirectResponse(url="/admin/tomorrow", status_code=303)


# -------------------------
# Events : open/close + planned
# -------------------------

@router.post("/admin/toggle")
def admin_toggle(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))

    event = get_event(event_date)
    if event:
        toggle_event_open(event["id"])

    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/toggle-planned")
def admin_toggle_planned(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))

    event = get_event(event_date)
    if event:
        toggle_event_planned(event["id"])

    return RedirectResponse("/admin", status_code=303)


# -------------------------
# Agents
# -------------------------

@router.get("/admin/agents", response_class=HTMLResponse)
def admin_agents(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    agents = list_agents(active_only=False)

    return _templates(request).TemplateResponse(
        "admin_agents.html",
        {"request": request, "agents": agents},
    )


@router.post("/admin/agents/add")
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


@router.post("/admin/agents/update")
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


@router.post("/admin/agents/delete")
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


@router.post("/admin/agents/toggle-active")
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


@router.post("/admin/agents/toggle-whatsapp")
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


# -------------------------
# Shifts + liens WhatsApp
# -------------------------

@router.get("/admin/shifts", response_class=HTMLResponse)
def admin_shifts(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    shift_date = _tomorrow_str()

    agents = list_agents(active_only=True)
    working_ids = list_working_agent_ids(shift_date)

    # Event de demain (menu auto)
    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))
    event = get_event(event_date)

    working_agents = list_working_agents_for_date(shift_date)

    wa_links = {}
    if event:
        menu_text = ", ".join(event["menu"])

        # sign_agent_link est stocké dans app.state
        sign_agent_link = request.app.state.sign_agent_link

        base_url = _base_url(request)

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

            wa_links[a["id"]] = _wa_me_link(a["phone"], msg)

    return _templates(request).TemplateResponse(
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


@router.post("/admin/shifts/save")
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



# -------------------------
# Foods
# -------------------------

@router.get("/admin/foods", response_class=HTMLResponse)
def admin_foods(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    foods = list_foods(active_only=False)

    return _templates(request).TemplateResponse(
        "admin_foods.html",
        {"request": request, "foods": foods},
    )


@router.post("/admin/foods/add")
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


@router.post("/admin/foods/toggle")
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


# -------------------------
# Recipes
# -------------------------

@router.get("/admin/recipes", response_class=HTMLResponse)
def admin_recipes(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    recipes = list_recipes(active_only=False)

    return _templates(request).TemplateResponse(
        "admin_recipes.html",
        {"request": request, "recipes": recipes},
    )


@router.post("/admin/recipes/add")
def admin_recipes_add(
    request: Request,
    name: str = Form(...),
):
    guard = require_admin(request)
    if guard:
        return guard

    add_recipe(name=name)
    return RedirectResponse("/admin/recipes", status_code=303)


@router.post("/admin/recipes/toggle")
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


# -------------------------
# Offers
# -------------------------

@router.get("/admin/offers", response_class=HTMLResponse)
def admin_offers(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    offer_date = _tomorrow_str()

    recipes = list_recipes(active_only=True)
    foods = list_foods(active_only=True)
    offers = list_offers_for_date(offer_date)

    mains = [o for o in offers if o["offer_type"] == "MAIN"]
    sides = [o for o in offers if o["offer_type"] == "SIDE"]

    return _templates(request).TemplateResponse(
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


@router.post("/admin/offers/add-main")
def admin_offers_add_main(
    request: Request,
    recipe_id: int = Form(...),
    max_per_person: int = Form(1),
):
    guard = require_admin(request)
    if guard:
        return guard

    add_offer_main(_tomorrow_str(), recipe_id, max_per_person)
    return RedirectResponse("/admin/offers", status_code=303)


@router.post("/admin/offers/add-side")
def admin_offers_add_side(
    request: Request,
    food_id: int = Form(...),
    max_per_person: int = Form(1),
):
    guard = require_admin(request)
    if guard:
        return guard

    add_offer_side(_tomorrow_str(), food_id, max_per_person)
    return RedirectResponse("/admin/offers", status_code=303)


@router.post("/admin/offers/update-max")
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


@router.post("/admin/offers/toggle")
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


@router.get("/admin/tomorrow", response_class=HTMLResponse)
def admin_tomorrow(request: Request):
    # Protection admin
    guard = require_admin(request)
    if guard:
        return guard

    event_date = _tomorrow_str()

    # On garantit l’event de demain
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))
    event = get_event(event_date)

    # Snapshot global "demain" déjà utilisé sur le dashboard
    snapshot = get_tomorrow_admin_snapshot(event_date)

    # Offres configurées
    offers = list_offers_for_date(event_date)
    mains = [o for o in offers if o["offer_type"] == "MAIN"]
    sides = [o for o in offers if o["offer_type"] == "SIDE"]

    # Catalogue utile pour composer l’offre directement depuis la page
    recipes = list_recipes(active_only=True)
    foods = list_foods(active_only=True)

    # Agents disponibles + sélectionnés demain
    agents = list_agents(active_only=True)
    working_ids = list_working_agent_ids(event_date)

    # On enrichit les agents avec un booléen simple pour le template
    for agent in agents:
        agent["selected_tomorrow"] = agent["id"] in working_ids

    return _templates(request).TemplateResponse(
        "admin_tomorrow.html",
        {
            "request": request,
            "event": event,
            "snapshot": snapshot,
            "mains": mains,
            "sides": sides,
            "recipes": recipes,
            "foods": foods,
            "agents": agents,
            "working_ids": working_ids,
        },
    )


@router.post("/admin/tomorrow/toggle-open")
def admin_tomorrow_toggle_open(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))

    event = get_event(event_date)
    new_open = 0 if event["open"] else 1
    update_event_flags(event_date, open_value=new_open)

    if request.headers.get("HX-Request") == "true":
        event = get_event(event_date)
        snapshot = get_tomorrow_admin_snapshot(event_date)

        offers = list_offers_for_date(event_date)
        mains = [o for o in offers if o["offer_type"] == "MAIN"]
        sides = [o for o in offers if o["offer_type"] == "SIDE"]

        agents = list_agents(active_only=True)
        working_ids = list_working_agent_ids(event_date)

        return _templates(request).TemplateResponse(
            "admin/_tomorrow_top.html",
            {
                "request": request,
                "event": event,
                "snapshot": snapshot,
                "mains": mains,
                "sides": sides,
                "agents": agents,
                "working_ids": working_ids,
            },
        )

    return RedirectResponse(url="/admin/tomorrow", status_code=303)


@router.post("/admin/tomorrow/toggle-planned")
def admin_tomorrow_toggle_planned(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))

    event = get_event(event_date)
    current_planned = 1 if event.get("is_planned", True) else 0
    new_planned = 0 if current_planned else 1
    update_event_flags(event_date, is_planned_value=new_planned)

    if request.headers.get("HX-Request") == "true":
        event = get_event(event_date)
        snapshot = get_tomorrow_admin_snapshot(event_date)

        offers = list_offers_for_date(event_date)
        mains = [o for o in offers if o["offer_type"] == "MAIN"]
        sides = [o for o in offers if o["offer_type"] == "SIDE"]

        agents = list_agents(active_only=True)
        working_ids = list_working_agent_ids(event_date)

        return _templates(request).TemplateResponse(
            "admin/_tomorrow_top.html",
            {
                "request": request,
                "event": event,
                "snapshot": snapshot,
                "mains": mains,
                "sides": sides,
                "agents": agents,
                "working_ids": working_ids,
            },
        )

    return RedirectResponse(url="/admin/tomorrow", status_code=303)

@router.post("/admin/tomorrow/update-agents")
async def admin_tomorrow_update_agents(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    form = await request.form()
    shift_date = form.get("shift_date")
    working_agent_ids_raw = form.getlist("working_agent_ids")

    working_agent_ids = []
    for value in working_agent_ids_raw:
        try:
            working_agent_ids.append(int(value))
        except (TypeError, ValueError):
            pass

    if shift_date:
        set_working_agents_for_date(shift_date, working_agent_ids)

    # Recharger les données nécessaires au partial
    event = get_event(shift_date)
    agents = list_agents(active_only=True)
    selected_ids = list_working_agent_ids(shift_date)

    for agent in agents:
        agent["selected_tomorrow"] = agent["id"] in selected_ids

    # Si la requête vient de HTMX, on renvoie juste le bloc agents
    if request.headers.get("HX-Request") == "true":
        return _templates(request).TemplateResponse(
            "admin/_tomorrow_agents.html",
            {
                "request": request,
                "event": event,
                "agents": agents,
                "save_success": True,
            },
        )

    # Fallback classique si HTMX n'est pas chargé
    return RedirectResponse(url="/admin/tomorrow", status_code=303)


@router.post("/admin/tomorrow/add-offer")
async def admin_tomorrow_add_offer(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    form = await request.form()

    event_date = form.get("date")
    offer_type = form.get("offer_type")
    max_per_person_raw = form.get("max_per_person")

    try:
        max_per_person = int(max_per_person_raw or 1)
    except (TypeError, ValueError):
        max_per_person = 1

    if max_per_person < 1:
        max_per_person = 1

    if event_date and offer_type == "MAIN":
        recipe_id_raw = form.get("recipe_id")
        try:
            recipe_id = int(recipe_id_raw)
            add_offer_main(event_date, recipe_id, max_per_person)
        except (TypeError, ValueError):
            pass

    elif event_date and offer_type == "SIDE":
        food_id_raw = form.get("food_id")
        try:
            food_id = int(food_id_raw)
            add_offer_side(event_date, food_id, max_per_person)
        except (TypeError, ValueError):
            pass

    # Recharger les données utiles au partial
    event = get_event(event_date)
    offers = list_offers_for_date(event_date)
    mains = [o for o in offers if o["offer_type"] == "MAIN"]
    sides = [o for o in offers if o["offer_type"] == "SIDE"]
    recipes = list_recipes(active_only=True)
    foods = list_foods(active_only=True)

    # Si la requête vient de HTMX, renvoyer juste le bloc Offre
    if request.headers.get("HX-Request") == "true":
        return _templates(request).TemplateResponse(
            "admin/_tomorrow_offers.html",
            {
                "request": request,
                "event": event,
                "mains": mains,
                "sides": sides,
                "recipes": recipes,
                "foods": foods,
                "save_success": True,
            },
        )

    return RedirectResponse(url="/admin/tomorrow", status_code=303)




@router.get("/admin/recipes/edit/{recipe_id}", response_class=HTMLResponse)
def admin_recipes_edit(request: Request, recipe_id: int):
    guard = require_admin(request)
    if guard:
        return guard

    recipe = get_recipe(recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recette introuvable")

    return _templates(request).TemplateResponse(
        "admin_recipe_edit.html",
        {"request": request, "recipe": recipe},
    )


@router.post("/admin/recipes/edit/{recipe_id}")
def admin_recipes_edit_post(
    request: Request,
    recipe_id: int,
    name: str = Form(...),
    is_active: bool = Form(False),
):
    guard = require_admin(request)
    if guard:
        return guard

    update_recipe(recipe_id, name=name, is_active=is_active)
    _flash(request, "✅ Recette mise à jour.")
    return RedirectResponse("/admin/recipes", status_code=303)
@router.post("/admin/tomorrow/update-offer-max")
async def update_offer_max_route(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    form = await request.form()

    offer_id = form.get("offer_id")
    event_date = form.get("date")
    max_raw = form.get("max_per_person")

    try:
        offer_id = int(offer_id)
        max_val = max(1, int(max_raw))
        update_offer_max(offer_id, max_val)
    except:
        pass

    return await _render_offers_partial(request, event_date)
@router.post("/admin/tomorrow/toggle-offer")
async def toggle_offer_route(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    form = await request.form()

    offer_id = form.get("offer_id")
    event_date = form.get("date")

    try:
        offer_id = int(offer_id)

        # récup état actuel
        offers = list_offers_for_date(event_date)
        offer = next((o for o in offers if o["id"] == offer_id), None)

        if offer:
            set_offer_active(offer_id, not offer["is_active"])
    except:
        pass

    return await _render_offers_partial(request, event_date)
async def _render_offers_partial(request: Request, event_date: str):
    event = get_event(event_date)
    offers = list_offers_for_date(event_date)

    mains = [o for o in offers if o["offer_type"] == "MAIN"]
    sides = [o for o in offers if o["offer_type"] == "SIDE"]

    recipes = list_recipes(active_only=True)
    foods = list_foods(active_only=True)

    return _templates(request).TemplateResponse(
        "admin/_tomorrow_offers.html",
        {
            "request": request,
            "event": event,
            "mains": mains,
            "sides": sides,
            "recipes": recipes,
            "foods": foods,
            "save_success": True,
        },
    )

@router.post("/admin/tomorrow/delete-offer")
async def delete_offer_route(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    form = await request.form()

    offer_id_raw = form.get("offer_id")
    event_date = form.get("date")

    try:
        offer_id = int(offer_id_raw)
        delete_offer(offer_id)
    except Exception:
        pass

    return await _render_offers_partial(request, event_date)

@router.get("/admin/tomorrow/top")
def admin_tomorrow_top(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))

    event = get_event(event_date)
    snapshot = get_tomorrow_admin_snapshot(event_date)

    offers = list_offers_for_date(event_date)
    mains = [o for o in offers if o["offer_type"] == "MAIN"]
    sides = [o for o in offers if o["offer_type"] == "SIDE"]

    agents = list_agents(active_only=True)
    working_ids = list_working_agent_ids(event_date)

    return _templates(request).TemplateResponse(
        "admin/_tomorrow_top.html",
        {
            "request": request,
            "event": event,
            "snapshot": snapshot,
            "mains": mains,
            "sides": sides,
            "agents": agents,
            "working_ids": working_ids,
        },
    )

@router.get("/admin/tomorrow/bottom")
def admin_tomorrow_bottom(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))

    event = get_event(event_date)
    snapshot = get_tomorrow_admin_snapshot(event_date)

    return _templates(request).TemplateResponse(
        "admin/_tomorrow_bottom.html",
        {
            "request": request,
            "event": event,
            "snapshot": snapshot,
        },
    )

@router.get("/admin/app", response_class=HTMLResponse)
def admin_app(request: Request):
    guard = require_admin(request)
    if guard:
        return guard

    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))

    event = get_event(event_date)
    snapshot = get_tomorrow_admin_snapshot(event_date)

    offers = list_offers_for_date(event_date)
    mains = [o for o in offers if o["offer_type"] == "MAIN"]
    sides = [o for o in offers if o["offer_type"] == "SIDE"]

    agents = list_agents(active_only=True)
    working_ids = list_working_agent_ids(event_date)

    recipes = list_recipes(active_only=True)
    foods = list_foods(active_only=True)

    return _templates(request).TemplateResponse(
        "admin_app.html",
        {
            "request": request,
            "event": event,
            "snapshot": snapshot,
            "mains": mains,
            "sides": sides,
            "agents": agents,
            "working_ids": working_ids,
            "recipes": recipes,
            "foods": foods,
        },
    )    

@router.get("/api/admin/daily-offer-state")
def api_admin_daily_offer_state(request: Request):
    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))

    event = get_event(event_date)
    offers = list_offers_for_date(event_date)
    recipes = list_recipes(active_only=True)
    foods = list_foods(active_only=True)

    frontend_recipes = []

    with get_conn() as conn:
        try:
            conn.execute("ALTER TABLE recipes ADD COLUMN image_url TEXT")
        except Exception:
            pass

        for recipe in recipes:
            recipe_row = conn.execute(
                """
                SELECT image_url
                FROM recipes
                WHERE id = ?
                """,
                (recipe["id"],),
            ).fetchone()

            ingredient_rows = conn.execute(
                """
                SELECT food_id, qty
                FROM recipe_ingredients
                WHERE recipe_id = ?
                ORDER BY id
                """,
                (recipe["id"],),
            ).fetchall()

            recipe_ingredients = []
            for row in ingredient_rows:
                recipe_ingredients.append({
                    "ingredientId": f"f-{row['food_id']}",
                    "quantity": float(row["qty"] or 0),
                })

            frontend_recipes.append({
                "id": f"r-{recipe['id']}",
                "name": recipe["name"],
                "category": "principal",
                "ingredients": recipe_ingredients,
                "imageUrl": recipe_row["image_url"] if recipe_row else None,
                "createdAt": None,
            })

    main_dishes = []
    accompaniments = []

    for offer in offers:
        if not offer["is_active"]:
            continue

        if offer["offer_type"] == "MAIN" and offer["recipe_id"]:
            main_dishes.append({
                "recipeId": f"r-{offer['recipe_id']}",
                "maxPerPerson": int(offer["max_per_person"]),
            })

        if offer["offer_type"] == "SIDE" and offer["food_id"]:
            accompaniments.append({
                "recipeId": f"f-{offer['food_id']}",
                "maxPerPerson": int(offer["max_per_person"]),
            })

    daily_offer = {
        "id": f"offer-{event['id']}",
        "date": event_date,
        "mainDishes": main_dishes,
        "accompaniments": accompaniments,
        "isPlanned": bool(event.get("is_planned", True)),
        "isOpen": bool(event["open"]),
        "createdAt": None,
    }

    frontend_ingredients = []

    with get_conn() as conn:
        try:
            conn.execute("ALTER TABLE foods ADD COLUMN stock REAL NOT NULL DEFAULT 0")
        except Exception:
            pass

        rows = conn.execute(
            """
            SELECT id, name, unit, stock, is_side, low_stock_threshold, image_url
            FROM foods
            WHERE is_active = 1
            ORDER BY name
            """
        ).fetchall()

    for food in rows:
        frontend_ingredients.append({
            "id": f"f-{food['id']}",
            "name": food["name"],
            "unit": food["unit"],
            "stock": float(food["stock"] or 0),
            "isSide": bool(food["is_side"]),
            "lowStockThreshold": float(food["low_stock_threshold"] or 0),
            "imageUrl": food["image_url"] or "",
        })

    return JSONResponse({
        "ingredients": frontend_ingredients,
        "recipes": frontend_recipes,
        "dailyOffer": daily_offer,
    })
@router.post("/api/admin/daily-offer-state")
def api_admin_save_daily_offer_state(request: Request, payload: dict = Body(...)):
    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))

    event = get_event(event_date)
    if not event:
        return JSONResponse({"error": "event_not_found"}, status_code=404)

    is_planned = bool(payload.get("isPlanned", True))
    is_open = bool(payload.get("isOpen", True))
    main_dishes = payload.get("mainDishes", [])
    accompaniments = payload.get("accompaniments", [])

    # 1) Mettre à jour l'event
    set_event_planned(event["id"], is_planned)

    # Si pas prévu, on ferme aussi les réservations
    if not is_planned:
        if event["open"]:
            toggle_event_open(event["id"])
    else:
        # on synchronise l'état open avec la valeur voulue
        current_open = bool(get_event(event_date)["open"])
        if current_open != is_open:
            toggle_event_open(event["id"])

    # 2) Remplacer toutes les offres du jour
    existing_offers = list_offers_for_date(event_date)
    for offer in existing_offers:
        set_offer_active(offer["id"], False)

    # 3) Réactiver / recréer les MAIN
    if is_planned:
        for item in main_dishes:
            recipe_id_raw = item.get("recipeId", "")
            max_per_person = int(item.get("maxPerPerson", 1))

            if recipe_id_raw.startswith("r-"):
                recipe_id = int(recipe_id_raw.replace("r-", ""))
                add_offer_main(event_date, recipe_id, max_per_person)

        # 4) Réactiver / recréer les SIDE
        for item in accompaniments:
            food_id_raw = item.get("recipeId", "")
            max_per_person = int(item.get("maxPerPerson", 1))

            if food_id_raw.startswith("f-"):
                food_id = int(food_id_raw.replace("f-", ""))
                add_offer_side(event_date, food_id, max_per_person)

    # 5) Retourner l'état relu depuis le backend
    offers = list_offers_for_date(event_date)
    recipes = list_recipes(active_only=True)
    foods = list_foods(active_only=True)
    refreshed_event = get_event(event_date)

    frontend_recipes = []
    frontend_ingredients = []

    with get_conn() as conn:
        try:
            conn.execute("ALTER TABLE recipes ADD COLUMN image_url TEXT")
        except Exception:
            pass

        try:
            conn.execute("ALTER TABLE foods ADD COLUMN stock REAL NOT NULL DEFAULT 0")
        except Exception:
            pass

        try:
            conn.execute("ALTER TABLE foods ADD COLUMN image_url TEXT")
        except Exception:
            pass

        try:
            conn.execute("ALTER TABLE foods ADD COLUMN low_stock_threshold REAL NOT NULL DEFAULT 0")
        except Exception:
            pass

        for recipe in recipes:
            recipe_row = conn.execute(
                """
                SELECT image_url
                FROM recipes
                WHERE id = ?
                """,
                (recipe["id"],),
            ).fetchone()

            ingredient_rows = conn.execute(
                """
                SELECT food_id, qty
                FROM recipe_ingredients
                WHERE recipe_id = ?
                ORDER BY id
                """,
                (recipe["id"],),
            ).fetchall()

            recipe_ingredients = []
            for row in ingredient_rows:
                recipe_ingredients.append({
                    "ingredientId": f"f-{row['food_id']}",
                    "quantity": float(row["qty"] or 0),
                })

            frontend_recipes.append({
                "id": f"r-{recipe['id']}",
                "name": recipe["name"],
                "category": "principal",
                "ingredients": recipe_ingredients,
                "imageUrl": recipe_row["image_url"] if recipe_row else "",
                "createdAt": None,
            })

        food_rows = conn.execute(
            """
            SELECT id, name, unit, stock, is_side, low_stock_threshold, image_url
            FROM foods
            WHERE is_active = 1
            ORDER BY name
            """
        ).fetchall()

        for food in food_rows:
            frontend_ingredients.append({
                "id": f"f-{food['id']}",
                "name": food["name"],
                "unit": food["unit"],
                "stock": float(food["stock"] or 0),
                "isSide": bool(food["is_side"]),
                "lowStockThreshold": float(food["low_stock_threshold"] or 0),
                "imageUrl": food["image_url"] or "",
            })

    refreshed_main = []
    refreshed_acc = []

    for offer in offers:
        if not offer["is_active"]:
            continue

        if offer["offer_type"] == "MAIN" and offer["recipe_id"]:
            refreshed_main.append({
                "recipeId": f"r-{offer['recipe_id']}",
                "maxPerPerson": int(offer["max_per_person"]),
            })

        if offer["offer_type"] == "SIDE" and offer["food_id"]:
            refreshed_acc.append({
                "recipeId": f"f-{offer['food_id']}",
                "maxPerPerson": int(offer["max_per_person"]),
            })

    daily_offer = {
        "id": f"offer-{refreshed_event['id']}",
        "date": event_date,
        "mainDishes": refreshed_main,
        "accompaniments": refreshed_acc,
        "isPlanned": bool(refreshed_event.get("is_planned", True)),
        "isOpen": bool(refreshed_event["open"]),
        "createdAt": None,
    }

    return JSONResponse({
        "success": True,
        "recipes": frontend_recipes,
        "ingredients": frontend_ingredients,
        "dailyOffer": daily_offer,
    })
@router.post("/api/admin/recipes")
def api_admin_create_recipe(request: Request, payload: dict = Body(...)):
    name = (payload.get("name") or "").strip()
    ingredients = payload.get("ingredients", [])
    image_url = (payload.get("imageUrl") or "").strip() or None

    if not name:
        return JSONResponse({"error": "missing_name"}, status_code=400)

    if not ingredients:
        return JSONResponse({"error": "missing_ingredients"}, status_code=400)

    # 1. créer la recette
    add_recipe(name)
    with get_conn() as conn:
        try:
            conn.execute("ALTER TABLE recipes ADD COLUMN image_url TEXT")
        except Exception:
            pass

        conn.execute(
            "UPDATE recipes SET image_url = ? WHERE name = ?",
            (image_url, name),
        )

    # 2. relire la recette créée pour récupérer son id
    recipes = list_recipes(active_only=False)
    created_recipe = next((r for r in recipes if r["name"] == name), None)

    if not created_recipe:
        return JSONResponse({"error": "recipe_not_created"}, status_code=500)

    recipe_id = created_recipe["id"]

    # 3. enregistrer les ingrédients de la recette
    with get_conn() as conn:
        conn.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))

        for item in ingredients:
            ingredient_id_raw = item.get("ingredientId", "")
            quantity = float(item.get("quantity", 0))

            if not ingredient_id_raw or quantity <= 0:
                continue

            if ingredient_id_raw.startswith("f-"):
                food_id = int(ingredient_id_raw.replace("f-", ""))
            else:
                food_id = int(ingredient_id_raw)

            conn.execute(
                """
                INSERT INTO recipe_ingredients (recipe_id, food_id, qty, unit)
                VALUES (?, ?, ?, 'unit')
                """,
                (recipe_id, food_id, quantity),
            )

    return JSONResponse({
        "success": True,
        "recipe": {
            "id": f"r-{recipe_id}",
            "name": name,
            "category": "principal",
            "ingredients": ingredients,
            "createdAt": None,
        },
    })

@router.delete("/api/admin/recipes/{recipe_id}")
def api_admin_delete_recipe(request: Request, recipe_id: int):
    event_date = _tomorrow_str()
    offers = list_offers_for_date(event_date)

    for offer in offers:
        if offer["is_active"] and offer["offer_type"] == "MAIN" and offer["recipe_id"] == recipe_id:
            return JSONResponse(
                {"error": "recipe_used_in_offer"},
                status_code=409,
            )

    with get_conn() as conn:
        conn.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
        conn.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))

    return JSONResponse({"success": True})

@router.post("/api/admin/foods")
def api_admin_create_food(request: Request, payload: dict = Body(...)):
    name = (payload.get("name") or "").strip()
    unit = (payload.get("unit") or "unit").strip()
    stock = payload.get("stock", 0)
    image_url = (payload.get("imageUrl") or "").strip() or None

    if not name:
        return JSONResponse({"error": "missing_name"}, status_code=400)
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM foods WHERE LOWER(name) = LOWER(?) LIMIT 1",
            (name,),
        ).fetchone()

    if existing:
        return JSONResponse({"error": "duplicate_food"}, status_code=409)    

    try:
        stock_value = float(stock)
    except (TypeError, ValueError):
        return JSONResponse({"error": "invalid_stock"}, status_code=400)

    if stock_value < 0:
        return JSONResponse({"error": "negative_stock"}, status_code=400)

    with get_conn() as conn:
        try:
            conn.execute("ALTER TABLE foods ADD COLUMN stock REAL NOT NULL DEFAULT 0")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE foods ADD COLUMN image_url TEXT")
        except Exception:
            pass

        conn.execute(
            "INSERT INTO foods (name, unit, is_active, stock, image_url) VALUES (?, ?, 1, ?, ?)",
            (name, unit, stock_value, image_url),
        )

        created_food = conn.execute(
            """
            SELECT id, name, unit, stock, is_side, low_stock_threshold, image_url
            FROM foods
            WHERE name = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (name,),
        ).fetchone()

    if not created_food:
        return JSONResponse({"error": "food_not_created"}, status_code=500)

    return JSONResponse({
        "success": True,
        "ingredient": {
            "id": f"f-{created_food['id']}",
            "name": created_food["name"],
            "unit": created_food["unit"],
            "stock": float(created_food["stock"] or 0),
            "isSide": bool(created_food["is_side"]),
            "lowStockThreshold": float(created_food["low_stock_threshold"] or 0),
            "imageUrl": created_food["image_url"] or "",
        },
    })

@router.patch("/api/admin/foods/{food_id}")
def api_admin_update_food(request: Request, food_id: int, payload: dict = Body(...)):
    name = (payload.get("name") or "").strip()
    unit = (payload.get("unit") or "").strip()
    stock = payload.get("stock", None)
    image_url = (payload.get("imageUrl") or "").strip() or None

    if not name:
        return JSONResponse({"error": "missing_name"}, status_code=400)

    if not unit:
        return JSONResponse({"error": "missing_unit"}, status_code=400)

    if stock is None:
        return JSONResponse({"error": "missing_stock"}, status_code=400)

    try:
        stock_value = float(stock)
    except (TypeError, ValueError):
        return JSONResponse({"error": "invalid_stock"}, status_code=400)

    if stock_value < 0:
        return JSONResponse({"error": "negative_stock"}, status_code=400)

    with get_conn() as conn:
        try:
            conn.execute("ALTER TABLE foods ADD COLUMN stock REAL NOT NULL DEFAULT 0")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE foods ADD COLUMN image_url TEXT")
        except Exception:
            pass

        existing = conn.execute(
            "SELECT id FROM foods WHERE id = ?",
            (food_id,),
        ).fetchone()

        if not existing:
            return JSONResponse({"error": "food_not_found"}, status_code=404)

        duplicate = conn.execute(
            """
            SELECT id
            FROM foods
            WHERE LOWER(name) = LOWER(?)
              AND id != ?
            LIMIT 1
            """,
            (name, food_id),
        ).fetchone()

        if duplicate:
            return JSONResponse({"error": "duplicate_food"}, status_code=409)

        conn.execute(
            """
            UPDATE foods
            SET name = ?, unit = ?, stock = ?, image_url = ?
            WHERE id = ?
            """,
            (name, unit, stock_value, image_url, food_id),
        )

        updated = conn.execute(
            """
            SELECT id, name, unit, stock, is_side, low_stock_threshold, image_url
            FROM foods
            WHERE id = ?
            """,
            (food_id,),
        ).fetchone()

    return JSONResponse({
        "success": True,
        "ingredient": {
            "id": f"f-{updated['id']}",
            "name": updated["name"],
            "unit": updated["unit"],
            "stock": float(updated["stock"] or 0),
            "isSide": bool(updated["is_side"]),
            "lowStockThreshold": float(updated["low_stock_threshold"] or 0),
            "imageUrl": updated["image_url"] or "",
        },
    })
@router.patch("/api/admin/foods/{food_id}/side")
def api_admin_update_food_side(request: Request, food_id: int, payload: dict = Body(...)):
    is_side = payload.get("isSide", None)

    if is_side is None:
        return JSONResponse({"error": "missing_is_side"}, status_code=400)

    with get_conn() as conn:
        food = conn.execute(
            "SELECT id FROM foods WHERE id = ?",
            (food_id,),
        ).fetchone()

        if not food:
            return JSONResponse({"error": "food_not_found"}, status_code=404)

        try:
            conn.execute("ALTER TABLE foods ADD COLUMN is_side INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass

        conn.execute(
            "UPDATE foods SET is_side = ? WHERE id = ?",
            (1 if bool(is_side) else 0, food_id),
        )

        updated = conn.execute(
            "SELECT id, name, unit, stock, is_side FROM foods WHERE id = ?",
            (food_id,),
        ).fetchone()

    return JSONResponse({
        "success": True,
        "ingredient": {
            "id": f"f-{updated['id']}",
            "name": updated["name"],
            "unit": updated["unit"],
            "stock": float(updated["stock"] or 0),
            "isSide": bool(updated["is_side"]),
        },
    })
@router.patch("/api/admin/foods/{food_id}/threshold")
def api_admin_update_food_threshold(request: Request, food_id: int, payload: dict = Body(...)):
    low_stock_threshold = payload.get("lowStockThreshold", None)

    if low_stock_threshold is None:
        return JSONResponse({"error": "missing_low_stock_threshold"}, status_code=400)

    try:
        threshold_value = float(low_stock_threshold)
    except (TypeError, ValueError):
        return JSONResponse({"error": "invalid_low_stock_threshold"}, status_code=400)

    if threshold_value < 0:
        return JSONResponse({"error": "negative_low_stock_threshold"}, status_code=400)

    with get_conn() as conn:
        try:
            conn.execute(
                "ALTER TABLE foods ADD COLUMN low_stock_threshold REAL NOT NULL DEFAULT 0"
            )
        except Exception:
            pass

        existing = conn.execute(
            "SELECT id FROM foods WHERE id = ?",
            (food_id,),
        ).fetchone()

        if not existing:
            return JSONResponse({"error": "food_not_found"}, status_code=404)

        conn.execute(
            "UPDATE foods SET low_stock_threshold = ? WHERE id = ?",
            (threshold_value, food_id),
        )

        updated = conn.execute(
            """
            SELECT id, name, unit, stock, is_side, low_stock_threshold
            FROM foods
            WHERE id = ?
            """,
            (food_id,),
        ).fetchone()

    return JSONResponse({
        "success": True,
        "ingredient": {
            "id": f"f-{updated['id']}",
            "name": updated["name"],
            "unit": updated["unit"],
            "stock": float(updated["stock"] or 0),
            "isSide": bool(updated["is_side"]),
            "lowStockThreshold": float(updated["low_stock_threshold"] or 0),
        },
    })
@router.delete("/api/admin/foods/{food_id}")
def api_admin_delete_food(request: Request, food_id: int):
    event_date = _tomorrow_str()
    offers = list_offers_for_date(event_date)

    for offer in offers:
        if offer["is_active"] and offer["offer_type"] == "SIDE" and offer["food_id"] == food_id:
            return JSONResponse(
                {"error": "food_used_in_offer"},
                status_code=409,
            )

    with get_conn() as conn:
        used_in_recipe = conn.execute(
            """
            SELECT 1
            FROM recipe_ingredients
            WHERE food_id = ?
            LIMIT 1
            """,
            (food_id,),
        ).fetchone()

        if used_in_recipe:
            return JSONResponse(
                {"error": "food_used_in_recipe"},
                status_code=409,
            )

        existing = conn.execute(
            "SELECT id FROM foods WHERE id = ?",
            (food_id,),
        ).fetchone()

        if not existing:
            return JSONResponse(
                {"error": "food_not_found"},
                status_code=404,
            )

        conn.execute("DELETE FROM foods WHERE id = ?", (food_id,))

    return JSONResponse({"success": True})
@router.patch("/api/admin/recipes/{recipe_id}")
def api_admin_update_recipe(request: Request, recipe_id: int, payload: dict = Body(...)):
    name = (payload.get("name") or "").strip()
    ingredients = payload.get("ingredients", [])
    image_url = (payload.get("imageUrl") or "").strip() or None
    

    if not name:
        return JSONResponse({"error": "missing_name"}, status_code=400)

    if not ingredients:
        return JSONResponse({"error": "missing_ingredients"}, status_code=400)

    with get_conn() as conn:
        # vérifier que la recette existe
        existing = conn.execute(
            "SELECT id FROM recipes WHERE id = ?",
            (recipe_id,),
        ).fetchone()

        if not existing:
            return JSONResponse({"error": "recipe_not_found"}, status_code=404)

        # mettre à jour le nom
        try:
            conn.execute("ALTER TABLE recipes ADD COLUMN image_url TEXT")
        except Exception:
            pass

        conn.execute(
            "UPDATE recipes SET name = ?, image_url = ? WHERE id = ?",
            (name, image_url, recipe_id),
        )

        # remplacer les ingrédients
        conn.execute(
            "DELETE FROM recipe_ingredients WHERE recipe_id = ?",
            (recipe_id,),
        )

        for item in ingredients:
            ingredient_id_raw = item.get("ingredientId", "")
            quantity = float(item.get("quantity", 0))

            if not ingredient_id_raw or quantity <= 0:
                continue

            if ingredient_id_raw.startswith("f-"):
                food_id = int(ingredient_id_raw.replace("f-", ""))
            else:
                food_id = int(ingredient_id_raw)

            conn.execute(
                """
                INSERT INTO recipe_ingredients (recipe_id, food_id, qty, unit)
                VALUES (?, ?, ?, 'unit')
                """,
                (recipe_id, food_id, quantity),
            )

    return JSONResponse({"success": True})

@router.get("/api/admin/recipes-state")
def api_admin_recipes_state(request: Request):
    with get_conn() as conn:
        recipe_rows = conn.execute(
            """
            SELECT id, name, is_active, image_url
            FROM recipes
            WHERE is_active = 1
            ORDER BY name
            """
        ).fetchall()

    frontend_ingredients = []
    frontend_recipes = []

    with get_conn() as conn:
        try:
            conn.execute("ALTER TABLE foods ADD COLUMN stock REAL NOT NULL DEFAULT 0")
        except Exception:
            pass

        food_rows = conn.execute(
            """
            SELECT id, name, unit, stock, is_side, low_stock_threshold, image_url
            FROM foods
            WHERE is_active = 1
            ORDER BY name
            """
        ).fetchall()

        for food in food_rows:
            frontend_ingredients.append({
            "id": f"f-{food['id']}",
            "name": food["name"],
            "unit": food["unit"],
            "stock": float(food["stock"] or 0),
            "isSide": bool(food["is_side"]),
            "lowStockThreshold": float(food["low_stock_threshold"] or 0),
            "imageUrl": food["image_url"] or "",
        })

        for recipe in recipe_rows:
            ingredient_rows = conn.execute(
                """
                SELECT food_id, qty
                FROM recipe_ingredients
                WHERE recipe_id = ?
                ORDER BY id
                """,
                (recipe["id"],),
            ).fetchall()

            recipe_ingredients = []
            for row in ingredient_rows:
                recipe_ingredients.append({
                    "ingredientId": f"f-{row['food_id']}",
                    "quantity": float(row["qty"] or 0),
                })

            frontend_recipes.append({
                "id": f"r-{recipe['id']}",
                "name": recipe["name"],
                "category": "principal",
                "ingredients": recipe_ingredients,
                "imageUrl": recipe["image_url"],
                "createdAt": None,
            })

    return JSONResponse({
        "ingredients": frontend_ingredients,
        "recipes": frontend_recipes,
    })
@router.get("/api/admin/agents-state")
def api_admin_agents_state(request: Request):
    agents = list_agents(active_only=False)

    frontend_agents = []
    for agent in agents:
        frontend_agents.append({
            "id": f"a-{agent['id']}",
            "name": agent["name"],
            "phone": agent["phone"],
            "whatsappOptin": bool(agent["whatsapp_optin"]),
            "isActive": bool(agent["is_active"]),
        })

    return JSONResponse({
        "agents": frontend_agents,
    })
@router.post("/api/admin/agents")
def api_admin_create_agent(request: Request, payload: dict = Body(...)):
    name = (payload.get("name") or "").strip()
    phone = (payload.get("phone") or "").strip()
    whatsapp_optin = bool(payload.get("whatsappOptin", True))

    if not name:
        return JSONResponse({"error": "missing_name"}, status_code=400)

    if not phone:
        return JSONResponse({"error": "missing_phone"}, status_code=400)

    add_agent(
        name=name,
        phone=phone,
        whatsapp_optin=whatsapp_optin,
        is_active=True,
    )

    agents = list_agents(active_only=False)
    created_agent = next(
        (a for a in reversed(agents) if a["name"] == name and a["phone"] == phone),
        None,
    )

    if not created_agent:
        return JSONResponse({"error": "agent_not_created"}, status_code=500)

    return JSONResponse({
        "success": True,
        "agent": {
            "id": f"a-{created_agent['id']}",
            "name": created_agent["name"],
            "phone": created_agent["phone"],
            "whatsappOptin": bool(created_agent["whatsapp_optin"]),
            "isActive": bool(created_agent["is_active"]),
        },
    })
@router.patch("/api/admin/agents/{agent_id}/active")
def api_admin_toggle_agent_active(request: Request, agent_id: int, payload: dict = Body(...)):
    is_active = payload.get("isActive", None)

    if is_active is None:
        return JSONResponse({"error": "missing_is_active"}, status_code=400)

    agents = list_agents(active_only=False)
    existing = next((a for a in agents if a["id"] == agent_id), None)

    if not existing:
        return JSONResponse({"error": "agent_not_found"}, status_code=404)

    set_agent_active(agent_id, bool(is_active))

    refreshed_agents = list_agents(active_only=False)
    updated = next((a for a in refreshed_agents if a["id"] == agent_id), None)

    if not updated:
        return JSONResponse({"error": "agent_not_found"}, status_code=404)

    return JSONResponse({
        "success": True,
        "agent": {
            "id": f"a-{updated['id']}",
            "name": updated["name"],
            "phone": updated["phone"],
            "whatsappOptin": bool(updated["whatsapp_optin"]),
            "isActive": bool(updated["is_active"]),
        },
    })
@router.get("/api/admin/users-state")
def api_admin_users_state(request: Request):
    users = list_users(active_only=False)

    frontend_users = []
    for user in users:
        frontend_users.append({
            "id": f"u-{user['id']}",
            "name": user["name"],
            "email": user["email"],
            "phone": user["phone"],
            "role": user["role"],
            "service": user["service"],
            "imageUrl": user["image_url"] or "",
            "isActive": bool(user["is_active"]),
        })

    return JSONResponse({
        "users": frontend_users,
    })
@router.post("/api/admin/users")
def api_admin_create_user(request: Request, payload: dict = Body(...)):
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    phone = (payload.get("phone") or "").strip()
    password = payload.get("password") or ""
    role = (payload.get("role") or "utilisateur").strip()
    service = (payload.get("service") or "").strip()
    image_url = (payload.get("imageUrl") or "").strip()

    if not name:
        return JSONResponse({"error": "missing_name"}, status_code=400)

    if not email:
        return JSONResponse({"error": "missing_email"}, status_code=400)

    if not password:
        return JSONResponse({"error": "missing_password"}, status_code=400)

    if role not in {"admin", "gestionnaire", "utilisateur"}:
        return JSONResponse({"error": "invalid_role"}, status_code=400)

    existing_users = list_users(active_only=False)
    duplicate = next((u for u in existing_users if u["email"].strip().lower() == email), None)
    if duplicate:
        return JSONResponse({"error": "duplicate_email"}, status_code=409)

    try:
        add_user(
            name=name,
            email=email,
            password_hash=_hash_password(password),
            phone=phone,
            role=role,
            service=service,
            image_url=image_url,
            is_active=True,
        )
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    users = list_users(active_only=False)
    created_user = next(
        (u for u in reversed(users) if u["email"].strip().lower() == email),
        None,
    )

    if not created_user:
        return JSONResponse({"error": "user_not_created"}, status_code=500)

    return JSONResponse({
        "success": True,
        "user": {
            "id": f"u-{created_user['id']}",
            "name": created_user["name"],
            "email": created_user["email"],
            "phone": created_user["phone"],
            "role": created_user["role"],
            "service": created_user["service"],
            "imageUrl": created_user["image_url"] or "",
            "isActive": bool(created_user["is_active"]),
        },
    })

@router.patch("/api/admin/users/{user_id}/active")
def api_admin_update_user_active(request: Request, user_id: int, payload: dict = Body(...)):
    is_active = payload.get("isActive", None)

    if is_active is None:
        return JSONResponse({"error": "missing_is_active"}, status_code=400)

    users = list_users(active_only=False)
    existing = next((u for u in users if u["id"] == user_id), None)

    if not existing:
        return JSONResponse({"error": "user_not_found"}, status_code=404)

    set_user_active(user_id, bool(is_active))

    refreshed_users = list_users(active_only=False)
    updated = next((u for u in refreshed_users if u["id"] == user_id), None)

    if not updated:
        return JSONResponse({"error": "user_not_found"}, status_code=404)

    return JSONResponse({
        "success": True,
        "user": {
            "id": f"u-{updated['id']}",
            "name": updated["name"],
            "email": updated["email"],
            "phone": updated["phone"],
            "role": updated["role"],
            "service": updated["service"],
            "imageUrl": updated["image_url"] or "",
            "isActive": bool(updated["is_active"]),
        },
    })

@router.delete("/api/admin/users/{user_id}")
def api_admin_delete_user(request: Request, user_id: int):
    users = list_users(active_only=False)
    existing = next((u for u in users if u["id"] == user_id), None)

    if not existing:
        return JSONResponse({"error": "user_not_found"}, status_code=404)

    delete_user(user_id)

    return JSONResponse({"success": True})

@router.patch("/api/admin/users/{user_id}")
def api_admin_update_user(request: Request, user_id: int, payload: dict = Body(...)):
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    phone = (payload.get("phone") or "").strip()
    role = (payload.get("role") or "utilisateur").strip()
    service = (payload.get("service") or "").strip()
    image_url = (payload.get("imageUrl") or "").strip()

    if not name:
        return JSONResponse({"error": "missing_name"}, status_code=400)

    if not email:
        return JSONResponse({"error": "missing_email"}, status_code=400)

    if role not in {"admin", "gestionnaire", "utilisateur"}:
        return JSONResponse({"error": "invalid_role"}, status_code=400)

    users = list_users(active_only=False)
    existing = next((u for u in users if u["id"] == user_id), None)

    if not existing:
        return JSONResponse({"error": "user_not_found"}, status_code=404)

    duplicate = next(
        (u for u in users if u["email"].strip().lower() == email and u["id"] != user_id),
        None,
    )
    if duplicate:
        return JSONResponse({"error": "duplicate_email"}, status_code=409)

    update_user(
        user_id=user_id,
        name=name,
        email=email,
        phone=phone,
        role=role,
        service=service,
        image_url=image_url,
    )

    refreshed_users = list_users(active_only=False)
    updated = next((u for u in refreshed_users if u["id"] == user_id), None)

    return JSONResponse({
        "success": True,
        "user": {
            "id": f"u-{updated['id']}",
            "name": updated["name"],
            "email": updated["email"],
            "phone": updated["phone"],
            "role": updated["role"],
            "service": updated["service"],
            "imageUrl": updated["image_url"] or "",
            "isActive": bool(updated["is_active"]),
        },
    })

@router.post("/api/auth/login")
def api_auth_login(request: Request, payload: dict = Body(...)):
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email:
        return JSONResponse({"error": "missing_email"}, status_code=400)

    if not password:
        return JSONResponse({"error": "missing_password"}, status_code=400)

    user = authenticate_user(email, _hash_password(password))

    if not user:
        return JSONResponse({"error": "invalid_credentials"}, status_code=401)

    request.session["user"] = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
    }

    return JSONResponse({
        "success": True,
        "user": {
            "id": f"u-{user['id']}",
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
        },
    })

@router.get("/api/auth/me")
def api_auth_me(request: Request):
    session_user = request.session.get("user")

    if not session_user:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)

    return JSONResponse({
        "user": {
            "id": f"u-{session_user['id']}",
            "name": session_user["name"],
            "email": session_user["email"],
            "role": session_user["role"],
        }
    }) 

@router.get("/api/admin/reservations-state")
def api_admin_reservations_state(request: Request):
    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))

    snapshot = get_tomorrow_admin_snapshot(event_date)
    event = snapshot.get("event")
    reservations = snapshot.get("reservations", [])
    totals = snapshot.get("totals", {})
    offers = snapshot.get("offers", {})

    frontend_reservations = []
    for index, reservation in enumerate(reservations, start=1):
        frontend_lines = []
        for line in reservation.get("lines", []):
            frontend_lines.append({
                "label": line.get("label") or "?",
                "qty": int(line.get("qty") or 0),
                "type": line.get("type") or "",
            })

        frontend_reservations.append({
            "id": f"res-{index}",
            "name": reservation.get("name") or "Inconnu",
            "lines": frontend_lines,
        })

    return JSONResponse({
        "date": event_date,
        "isPlanned": bool(event.get("is_planned", True)) if event else False,
        "isOpen": bool(event["open"]) if event else False,
        "reservations": frontend_reservations,
        "totals": {
            "mains": totals.get("mains", {}),
            "sides": totals.get("sides", {}),
        },
        "offers": {
            "mains": offers.get("mains", []),
            "sides": offers.get("sides", []),
        },
    })   

@router.post("/api/auth/logout")
def api_auth_logout(request: Request):
    request.session.pop("user", None)
    request.session.pop("admin", None)
    return JSONResponse({"success": True})    

@router.post("/api/employee/reservation")
def api_employee_create_reservation(request: Request, payload: dict = Body(...)):
    session_user = request.session.get("user")
    if not session_user:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)
    if session_user.get("role") != "utilisateur":
        return JSONResponse({"error": "forbidden"}, status_code=403)

    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))
    event = get_event(event_date)

    if not event:
        return JSONResponse({"error": "event_not_found"}, status_code=404)

    if not event.get("is_planned", True):
        return JSONResponse({"error": "event_not_planned"}, status_code=409)

    if not event.get("open", False):
        return JSONResponse({"error": "reservations_closed"}, status_code=409)

    main_dishes = payload.get("mainDishes", {})
    accompaniments = payload.get("accompaniments", {})

    if not isinstance(main_dishes, dict) or len(main_dishes) == 0:
        return JSONResponse({"error": "missing_main_dishes"}, status_code=400)

    offers = list_active_offers_for_date(event_date)
    active_mains = offers.get("mains", [])
    active_sides = offers.get("sides", [])

    all_offer_lines: list[tuple[int, int]] = []

    # Plats principaux
    for recipe_id, qty_raw in main_dishes.items():
        try:
            qty = int(qty_raw)
        except (TypeError, ValueError):
            continue

        if qty <= 0:
            continue

        main_offer = next(
            (o for o in active_mains if f"r-{o['recipe_id']}" == recipe_id),
            None,
        )
        if not main_offer:
            return JSONResponse({"error": "invalid_main_dish"}, status_code=400)

        max_per_person = int(main_offer.get("max_per_person") or 1)
        if qty > max_per_person:
            return JSONResponse({"error": "main_dish_quantity_exceeded"}, status_code=400)

        all_offer_lines.append((int(main_offer["id"]), qty))

    if len(all_offer_lines) == 0:
        return JSONResponse({"error": "missing_main_dishes"}, status_code=400)

    # Accompagnements
    for recipe_id, qty_raw in accompaniments.items():
        try:
            qty = int(qty_raw)
        except (TypeError, ValueError):
            continue

        if qty <= 0:
            continue

        side_offer = next(
            (o for o in active_sides if f"f-{o['food_id']}" == recipe_id),
            None,
        )
        if not side_offer:
            return JSONResponse({"error": "invalid_accompaniment"}, status_code=400)

        max_per_person = int(side_offer.get("max_per_person") or 1)
        if qty > max_per_person:
            return JSONResponse({"error": "accompaniment_quantity_exceeded"}, status_code=400)

        all_offer_lines.append((int(side_offer["id"]), qty))

    employee_name = session_user["name"]

    # Remplace l’ancienne réservation éventuelle
    delete_reservation_for_event_and_name(event["id"], employee_name)

    reservation_id = create_reservation(
        event_id=event["id"],
        name=employee_name,
        bring="",
    )

    set_reservation_lines(reservation_id, all_offer_lines)

    return JSONResponse({"success": True})

@router.get("/api/employee/reservation")
def api_employee_get_reservation(request: Request):
    session_user = request.session.get("user")
    if not session_user:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)

    if session_user.get("role") != "utilisateur":
        return JSONResponse({"error": "forbidden"}, status_code=403)

    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))
    event = get_event(event_date)

    if not event:
        return JSONResponse({"error": "event_not_found"}, status_code=404)

    reservations = list_reservations_with_lines(event["id"])
    current = next(
        (r for r in reservations if (r.get("name") or "").strip() == (session_user.get("name") or "").strip()),
        None,
    )

    if not current:
        return JSONResponse({
            "date": event_date,
            "reservation": None,
        })

    main_dishes = {}
    accompaniments = {}

    main_offers = list_active_offers_for_date(event_date).get("mains", [])
    side_offers = list_active_offers_for_date(event_date).get("sides", [])

    for line in current.get("lines", []):
        label = line.get("label")
        qty = int(line.get("qty") or 0)
        line_type = line.get("type")

        if qty <= 0:
            continue

        if line_type == "MAIN":
            match = next((o for o in main_offers if o.get("label") == label), None)
            if match and match.get("recipe_id"):
                main_dishes[f"r-{match['recipe_id']}"] = qty

        elif line_type == "SIDE":
            match = next((o for o in side_offers if o.get("label") == label), None)
            if match and match.get("food_id"):
                accompaniments[f"f-{match['food_id']}"] = qty

    return JSONResponse({
        "date": event_date,
        "reservation": {
            "mainDishes": main_dishes,
            "accompaniments": accompaniments,
        },
    })
@router.delete("/api/employee/reservation")
def api_employee_delete_reservation(request: Request):
    session_user = request.session.get("user")
    if not session_user:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)

    if session_user.get("role") != "utilisateur":
        return JSONResponse({"error": "forbidden"}, status_code=403)

    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))
    event = get_event(event_date)

    if not event:
        return JSONResponse({"error": "event_not_found"}, status_code=404)

    delete_reservation_for_event_and_name(event["id"], session_user["name"])

    return JSONResponse({"success": True})


@router.get("/api/admin/breakfast-price")
def api_admin_get_breakfast_price(request: Request):
    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))

    event = get_event(event_date)
    if not event:
        return JSONResponse({"error": "event_not_found"}, status_code=404)

    return JSONResponse({
        "date": event_date,
        "breakfastPrice": float(event.get("breakfast_price", 2.5)),
    })

@router.patch("/api/admin/breakfast-price")
def api_admin_update_breakfast_price(request: Request, payload: dict = Body(...)):
    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))

    breakfast_price = payload.get("breakfastPrice", None)

    if breakfast_price is None:
        return JSONResponse({"error": "missing_breakfast_price"}, status_code=400)

    try:
        breakfast_price_value = float(breakfast_price)
    except (TypeError, ValueError):
        return JSONResponse({"error": "invalid_breakfast_price"}, status_code=400)

    if breakfast_price_value <= 0:
        return JSONResponse({"error": "negative_or_zero_breakfast_price"}, status_code=400)

    set_event_breakfast_price(event_date, breakfast_price_value)

    event = get_event(event_date)
    if not event:
        return JSONResponse({"error": "event_not_found"}, status_code=404)

    return JSONResponse({
        "success": True,
        "date": event_date,
        "breakfastPrice": float(event.get("breakfast_price", 2.5)),
    })

@router.get("/api/employee/breakfast-info")
def api_employee_breakfast_info(request: Request):
    session_user = request.session.get("user")
    if not session_user:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)

    if session_user.get("role") != "utilisateur":
        return JSONResponse({"error": "forbidden"}, status_code=403)

    event_date = _tomorrow_str()
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))

    event = get_event(event_date)
    if not event:
        return JSONResponse({"error": "event_not_found"}, status_code=404)

    return JSONResponse({
        "date": event_date,
        "breakfastPrice": float(event.get("breakfast_price", 2.5)),
        "paymentMessage": "Le paiement se fera par Payconiq le jour du petit-déjeuner.",
    })    