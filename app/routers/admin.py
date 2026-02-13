# app/routers/admin.py

from __future__ import annotations

from datetime import date, timedelta
import urllib.parse
from typing import Optional

from fastapi import APIRouter, Form, Request,  HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

# + importe get_recipe, update_recipe

from app.auth import admin_credentials_ok, is_admin_logged_in, require_admin
from app.db import (
    # events
    ensure_event_for_date,
    get_event,
    toggle_event_open,
    toggle_event_planned,
    get_tomorrow_admin_snapshot,
    # agents
    list_agents,
    add_agent,
    update_agent,
    set_agent_active,
    set_agent_whatsapp_optin,
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


@router.post("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


# -------------------------
# Dashboard admin
# -------------------------

@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    # Protection admin
    guard = require_admin(request)
    if guard:
        return guard

    # Flash message éventuel
    flash_data = request.app.state.pop_flash(request)

    event_date = _tomorrow_str()
    tomorrow_date = date.today() + timedelta(days=1)

    # On garantit l’event de demain
    ensure_event_for_date(
        event_date,
        request.app.state.menu_for_date(tomorrow_date)
    )

    snapshot = get_tomorrow_admin_snapshot(event_date)

    return request.app.state.templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "flash": flash_data,
            "snapshot": snapshot,
        },
    )


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

    # On garantit l'event de demain
    ensure_event_for_date(event_date, _menu_for_tomorrow(request))
    event = get_event(event_date)

    offers = list_offers_for_date(event_date)

    mains = [o for o in offers if o["offer_type"] == "MAIN"]
    sides = [o for o in offers if o["offer_type"] == "SIDE"]

    return _templates(request).TemplateResponse(
        "admin_tomorrow.html",
        {
            "request": request,
            "event": event,
            "mains": mains,
            "sides": sides,
        },
    )
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
