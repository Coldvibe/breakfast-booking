"""
app/routers/public.py

Routes publiques:
- GET  /        : page de réservation (affichage + état "can_reserve" + message unique)
- POST /reserve : enregistrement d'une réservation (refus si pas de lien signé)

Le but:
- main.py reste "wiring" + admin
- la logique publique est isolée ici
"""

from datetime import date, timedelta
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse

from app.db import (
    ensure_event_for_date,
    get_event,
    list_active_offers_for_date,
    list_reservations_with_lines,
    list_agents,
    list_working_agent_ids,
    list_offers_for_date,
    create_reservation,
    set_reservation_lines,
    reservation_exists_for_event,
)

router = APIRouter()

@router.get("/service-worker.js")
def service_worker():
    # On sert le service worker à la racine pour qu'il couvre toute l'app
    sw_path = Path(__file__).resolve().parent.parent / "static" / "service-worker.js"
    return FileResponse(sw_path, media_type="application/javascript")

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    # Helpers injectés dans app.state depuis main.py
    templates = request.app.state.templates
    pop_flash = request.app.state.pop_flash
    tomorrow_str = request.app.state.tomorrow_str
    menu_for_date = request.app.state.menu_for_date
    verify_agent_link = request.app.state.verify_agent_link

    event_date = tomorrow_str()
    tomorrow_date = date.today() + timedelta(days=1)

    # Garantir que l'event de demain existe (menu auto)
    ensure_event_for_date(event_date, menu_for_date(tomorrow_date))

    event = get_event(event_date)
    if not event:
        return HTMLResponse("Event introuvable", status_code=500)

    # Offres actives pour demain
    offers = list_active_offers_for_date(event_date)
    mains = offers["mains"]
    sides = offers["sides"]

    # Réservations (avec lignes)
    reservations = list_reservations_with_lines(event["id"])

    # Flash message (affiché une seule fois)
    flash_data = pop_flash(request)

    # -------------------------
    # Lien signé (agent + date + token)
    # -------------------------
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

            # Important: la date du lien doit matcher l'event affiché
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
    no_offers = (len(mains) == 0 and len(sides) == 0)

    # Déjà réservé ? (seulement si lien valide + nom sûr)
    already_reserved = False
    if from_link and prefill_name:
        already_reserved = reservation_exists_for_event(event["id"], prefill_name)

    # -------------------------
    # Message unique (remplace le form)
    # -------------------------
    reserve_reason = None
    reserve_message = None

    # Priorités: planned -> open -> secure -> already -> no_offers
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


@router.post("/reserve")
async def reserve(request: Request):
    # Helpers injectés dans app.state depuis main.py
    flash = request.app.state.flash
    tomorrow_str = request.app.state.tomorrow_str
    menu_for_date = request.app.state.menu_for_date
    verify_agent_link = request.app.state.verify_agent_link

    form = await request.form()
    bring = (form.get("bring") or "").strip()

    event_date = tomorrow_str()
    tomorrow_date = date.today() + timedelta(days=1)

    # Garantir l'event de demain
    ensure_event_for_date(event_date, menu_for_date(tomorrow_date))
    event = get_event(event_date)

    if not event:
        flash(request, "Event introuvable.", "error")
        return RedirectResponse("/", status_code=303)

    # Si pas de petit-déj ou réservations fermées => refuse
    if not event.get("is_planned", True):
        flash(request, "Pas de petit-déjeuner prévu demain.", "error")
        return RedirectResponse("/", status_code=303)

    if not event["open"]:
        flash(request, "Réservations fermées.", "error")
        return RedirectResponse("/", status_code=303)

    # -------------------------
    # Sécurité: lien signé obligatoire
    # -------------------------
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

    # Bonus: l'agent doit être dans les agents "de demain"
    working_ids = list_working_agent_ids(event_date)
    if aid not in set(working_ids):
        flash(request, "Lien non autorisé pour cet événement.", "error")
        return RedirectResponse("/", status_code=303)

    # On force le nom depuis la DB (pas depuis le form)
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

    # -------------------------
    # Validation des offres côté serveur
    # -------------------------
    offers_list = list_offers_for_date(event_date)
    if not offers_list:
        flash(request, "Aucune offre n’est définie pour demain.", "error")
        return RedirectResponse(f"/?agent={aid}&d={event_date}&k={k_q}", status_code=303)

    offers_by_id = {o["id"]: o for o in offers_list}
    lines: list[tuple[int, int]] = []

    # MAIN (choix unique)
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

    # SIDE (quantités multiples)
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

    # Protection: refuser > 1 MAIN (requête forgée)
    main_count = sum(
        1
        for offer_id, qty in lines
        if qty > 0
        and offers_by_id.get(offer_id)
        and offers_by_id[offer_id].get("offer_type") == "MAIN"
    )
    if main_count > 1:
        flash(request, "Choix invalide (un seul plat).", "error")
        return RedirectResponse(f"/?agent={aid}&d={event_date}&k={k_q}", status_code=303)

    # Au moins un choix ou un bring
    if not lines and not bring:
        flash(request, "Choisis au moins un plat / accompagnement, ou indique ce que tu ramènes.", "warning")
        return RedirectResponse(f"/?agent={aid}&d={event_date}&k={k_q}", status_code=303)

    # Persist
    reservation_id = create_reservation(event["id"], name, bring)
    if lines:
        set_reservation_lines(reservation_id, lines)

    flash(request, "✅ Réservation enregistrée !", "success")
    return RedirectResponse(f"/?agent={aid}&d={event_date}&k={k_q}", status_code=303)
