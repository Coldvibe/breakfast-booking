# app/routers/admin.py

from __future__ import annotations

from datetime import date, timedelta
import urllib.parse
from typing import Optional

from fastapi import APIRouter, Form, Request,  HTTPException, Request, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

# + importe get_recipe, update_recipe

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
    
)

router = APIRouter()


# -------------------------
# Helpers (petits utils)
# -------------------------

def _tomorrow_str() -> str:
    # On centralise le "demain" pour éviter de répéter partout
    return (date.today() + timedelta(days=1)).isoformat()


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
            "SELECT id, name, unit, stock, is_side FROM foods WHERE is_active = 1 ORDER BY name"
        ).fetchall()

    for food in rows:
        frontend_ingredients.append({
            "id": f"f-{food['id']}",
            "name": food["name"],
            "unit": food["unit"],
            "stock": float(food["stock"] or 0),
            "isSide": bool(food["is_side"]),
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

    with get_conn() as conn:
        for recipe in recipes:
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
                "createdAt": None,
            })

    for food in foods:
        frontend_recipes.append({
            "id": f"f-{food['id']}",
            "name": food["name"],
            "category": "accompagnement",
            "ingredients": [],
            "createdAt": None,
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

        conn.execute(
            "INSERT INTO foods (name, unit, is_active, stock) VALUES (?, ?, 1, ?)",
            (name, unit, stock_value),
        )

        created_food = conn.execute(
            "SELECT id, name, unit, stock FROM foods WHERE name = ? ORDER BY id DESC LIMIT 1",
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
        },
    })

@router.patch("/api/admin/foods/{food_id}")
def api_admin_update_food(request: Request, food_id: int, payload: dict = Body(...)):
    stock = payload.get("stock", None)

    if stock is None:
        return JSONResponse({"error": "missing_stock"}, status_code=400)

    try:
        stock_value = float(stock)
    except (TypeError, ValueError):
        return JSONResponse({"error": "invalid_stock"}, status_code=400)

    if stock_value < 0:
        return JSONResponse({"error": "negative_stock"}, status_code=400)

    with get_conn() as conn:
        # On ajoute une colonne stock si elle n'existe pas encore
        try:
            conn.execute("ALTER TABLE foods ADD COLUMN stock REAL NOT NULL DEFAULT 0")
        except Exception:
            pass

        conn.execute(
            "UPDATE foods SET stock = ? WHERE id = ?",
            (stock_value, food_id),
        )

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
            "SELECT id, name, unit, stock, is_side FROM foods WHERE is_active = 1 ORDER BY name"
        ).fetchall()

        for food in food_rows:
            frontend_ingredients.append({
                "id": f"f-{food['id']}",
                "name": food["name"],
                "unit": food["unit"],
                "stock": float(food["stock"] or 0),
                "isSide": bool(food["is_side"]),
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