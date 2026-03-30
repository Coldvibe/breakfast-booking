import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "app.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_date TEXT NOT NULL UNIQUE,
                menu_json TEXT NOT NULL,
                is_open INTEGER NOT NULL DEFAULT 1
            );
            """
        )

        # --- migration safe: ajout du flag "is_planned" (petit-déj prévu ?) ---
        # 1 = prévu, 0 = pas de petit-déj
        try:
            conn.execute(
                "ALTER TABLE events ADD COLUMN is_planned INTEGER NOT NULL DEFAULT 1"
            )
        except Exception:
            # colonne déjà existante -> OK
            pass
        try:
            conn.execute(
                "ALTER TABLE events ADD COLUMN breakfast_price REAL NOT NULL DEFAULT 2.5"
            )
        except Exception:
            pass

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                items_json TEXT NOT NULL,
                bring TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(event_id) REFERENCES events(id)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                whatsapp_optin INTEGER NOT NULL DEFAULT 1,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shift_date TEXT NOT NULL,
                agent_id INTEGER NOT NULL,
                UNIQUE(shift_date, agent_id),
                FOREIGN KEY(agent_id) REFERENCES agents(id)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS foods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                unit TEXT NOT NULL DEFAULT 'unit',
                is_active INTEGER NOT NULL DEFAULT 1
            );
            """
        )
        try:
            conn.execute(
                "ALTER TABLE foods ADD COLUMN is_side INTEGER NOT NULL DEFAULT 0"
            )
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE foods ADD COLUMN low_stock_threshold REAL NOT NULL DEFAULT 0")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE foods ADD COLUMN image_url TEXT")
        except Exception:
            pass        
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                is_active INTEGER NOT NULL DEFAULT 1
            );
            """
        )
        try:
            conn.execute(
                "ALTER TABLE recipes ADD COLUMN image_url TEXT"
            )
        except Exception:
            pass
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recipe_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                food_id INTEGER NOT NULL,
                qty REAL NOT NULL DEFAULT 1,
                unit TEXT NOT NULL DEFAULT 'unit',
                FOREIGN KEY(recipe_id) REFERENCES recipes(id),
                FOREIGN KEY(food_id) REFERENCES foods(id)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                offer_date TEXT NOT NULL,                 -- YYYY-MM-DD
                offer_type TEXT NOT NULL,                 -- 'MAIN' or 'SIDE'
                recipe_id INTEGER,                        -- si MAIN
                food_id INTEGER,                          -- si SIDE
                max_per_person INTEGER NOT NULL DEFAULT 1,
                is_active INTEGER NOT NULL DEFAULT 1,

                CHECK (offer_type IN ('MAIN','SIDE')),
                CHECK (
                  (offer_type='MAIN' AND recipe_id IS NOT NULL AND food_id IS NULL) OR
                  (offer_type='SIDE' AND food_id IS NOT NULL AND recipe_id IS NULL)
                )
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_offers_date ON offers(offer_date);")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reservation_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reservation_id INTEGER NOT NULL,
                offer_id INTEGER NOT NULL,
                qty INTEGER NOT NULL,
                FOREIGN KEY(reservation_id) REFERENCES reservations(id) ON DELETE CASCADE,
                FOREIGN KEY(offer_id) REFERENCES offers(id) ON DELETE CASCADE
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_res_lines_res ON reservation_lines(reservation_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_res_lines_offer ON reservation_lines(offer_id);")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT NOT NULL DEFAULT '',
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'utilisateur',
                service TEXT NOT NULL DEFAULT '',
                image_url TEXT NOT NULL DEFAULT '',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                CHECK (role IN ('admin', 'gestionnaire', 'utilisateur'))
            );
            """
        )
        try:
            conn.execute("ALTER TABLE users ADD COLUMN phone TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass

        try:
            conn.execute("ALTER TABLE users ADD COLUMN password_hash TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass

        try:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'utilisateur'")
        except Exception:
            pass

        try:
            conn.execute("ALTER TABLE users ADD COLUMN service TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass

        try:
            conn.execute("ALTER TABLE users ADD COLUMN image_url TEXT NOT NULL DEFAULT ''")
        except Exception:
            pass

        try:
            conn.execute("ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1")
        except Exception:
            pass

        try:
            conn.execute("ALTER TABLE users ADD COLUMN created_at TEXT NOT NULL DEFAULT (datetime('now'))")
        except Exception:
            pass


# -------------------------
# EVENTS
# -------------------------

def ensure_event_for_date(event_date: str, default_menu: List[str]) -> None:
    """Crée l'event si absent. Par défaut: ouvert + petit-déj prévu.
    Le prix du petit-déj reprend celui de la veille si disponible, sinon 2.5.
    """
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM events WHERE event_date = ?",
            (event_date,),
        ).fetchone()
        if row:
            return

        previous_row = conn.execute(
            """
            SELECT breakfast_price
            FROM events
            WHERE event_date < ?
            ORDER BY event_date DESC
            LIMIT 1
            """,
            (event_date,),
        ).fetchone()

        breakfast_price = 2.5
        if previous_row and previous_row["breakfast_price"] is not None:
            breakfast_price = float(previous_row["breakfast_price"])

        conn.execute(
            """
            INSERT INTO events (event_date, menu_json, is_open, is_planned, breakfast_price)
            VALUES (?, ?, 1, 1, ?)
            """,
            (event_date, json.dumps(default_menu, ensure_ascii=False), breakfast_price),
        )


def get_event(event_date: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, event_date, menu_json, is_open, is_planned, breakfast_price
            FROM events
            WHERE event_date = ?
            """,
            (event_date,),
        ).fetchone()
        if not row:
            return None

        return {
            "id": row["id"],
            "date": row["event_date"],
            "menu": json.loads(row["menu_json"]),
            "open": bool(row["is_open"]),
            "is_planned": bool(row["is_planned"]),
            "breakfast_price": float(row["breakfast_price"] or 2.5),
        }


def toggle_event_open(event_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE events SET is_open = CASE is_open WHEN 1 THEN 0 ELSE 1 END WHERE id = ?",
            (event_id,),
        )


def toggle_event_planned(event_id: int) -> None:
    """ON/OFF: petit-déj prévu demain."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE events SET is_planned = CASE is_planned WHEN 1 THEN 0 ELSE 1 END WHERE id = ?",
            (event_id,),
        )


def set_event_planned(event_id: int, is_planned: bool) -> None:
    """Setter explicite (optionnel mais pratique)."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE events SET is_planned = ? WHERE id = ?",
            (1 if is_planned else 0, event_id),
        )

# -------------------------
# RESERVATIONS (legacy list)
# -------------------------

def list_reservations(event_id: int) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, name, items_json, bring, created_at
            FROM reservations
            WHERE event_id = ?
            ORDER BY id DESC
            """,
            (event_id,),
        ).fetchall()

        return [
            {
                "id": r["id"],
                "name": r["name"],
                "items": json.loads(r["items_json"]) if r["items_json"] else [],
                "bring": r["bring"] or "",
                "created_at": r["created_at"],
            }
            for r in rows
        ]


def add_reservation(event_id: int, name: str, items: List[str], bring: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO reservations (event_id, name, items_json, bring)
            VALUES (?, ?, ?, ?)
            """,
            (event_id, name, json.dumps(items, ensure_ascii=False), bring),
        )


# -------------------------
# AGENTS
# -------------------------

def list_agents(active_only: bool = False) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        if active_only:
            rows = conn.execute(
                """
                SELECT id, name, phone, whatsapp_optin, is_active, created_at
                FROM agents
                WHERE is_active = 1
                ORDER BY name COLLATE NOCASE
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, name, phone, whatsapp_optin, is_active, created_at
                FROM agents
                ORDER BY name COLLATE NOCASE
                """
            ).fetchall()

        return [
            {
                "id": r["id"],
                "name": r["name"],
                "phone": r["phone"],
                "whatsapp_optin": bool(r["whatsapp_optin"]),
                "is_active": bool(r["is_active"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]


def add_agent(name: str, phone: str, whatsapp_optin: bool = True, is_active: bool = True) -> None:
    clean_name = name.strip()
    clean_phone = phone.strip()

    if not clean_name:
        raise ValueError("Agent name is required")
    if not clean_phone:
        raise ValueError("Agent phone is required")

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO agents (name, phone, whatsapp_optin, is_active)
            VALUES (?, ?, ?, ?)
            """,
            (clean_name, clean_phone, 1 if whatsapp_optin else 0, 1 if is_active else 0),
        )


def set_agent_active(agent_id: int, is_active: bool) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE agents SET is_active = ? WHERE id = ?",
            (1 if is_active else 0, agent_id),
        )


def set_agent_whatsapp_optin(agent_id: int, whatsapp_optin: bool) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE agents SET whatsapp_optin = ? WHERE id = ?",
            (1 if whatsapp_optin else 0, agent_id),
        )


def update_agent(agent_id: int, name: str, phone: str, whatsapp_optin: bool, is_active: bool) -> None:
    clean_name = name.strip()
    clean_phone = phone.strip()

    if not clean_name:
        raise ValueError("Agent name is required")
    if not clean_phone:
        raise ValueError("Agent phone is required")

    with get_conn() as conn:
        conn.execute(
            """
            UPDATE agents
            SET name = ?, phone = ?, whatsapp_optin = ?, is_active = ?
            WHERE id = ?
            """,
            (clean_name, clean_phone, 1 if whatsapp_optin else 0, 1 if is_active else 0, agent_id),
        )

# -------------------------
# USERS
# -------------------------

def list_users(active_only: bool = False) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        if active_only:
            rows = conn.execute(
                """
                SELECT id, name, email, phone, role, service, image_url, is_active, created_at
                FROM users
                WHERE is_active = 1
                ORDER BY name COLLATE NOCASE
                """
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, name, email, phone, role, service, image_url, is_active, created_at
                FROM users
                ORDER BY name COLLATE NOCASE
                """
            ).fetchall()

        return [
            {
                "id": r["id"],
                "name": r["name"],
                "email": r["email"],
                "phone": r["phone"],
                "role": r["role"],
                "service": r["service"],
                "image_url": r["image_url"],
                "is_active": bool(r["is_active"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]


def add_user(
    name: str,
    email: str,
    password_hash: str,
    phone: str = "",
    role: str = "utilisateur",
    service: str = "",
    image_url: str = "",
    is_active: bool = True,
) -> None:
    clean_name = name.strip()
    clean_email = email.strip().lower()
    clean_phone = (phone or "").strip()
    clean_role = (role or "utilisateur").strip()
    clean_service = (service or "").strip()
    clean_image_url = (image_url or "").strip()

    if not clean_name:
        raise ValueError("User name is required")
    if not clean_email:
        raise ValueError("User email is required")
    if not password_hash:
        raise ValueError("User password hash is required")
    if clean_role not in {"admin", "gestionnaire", "utilisateur"}:
        raise ValueError("Invalid user role")

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (
                name, email, phone, password_hash, role, service, image_url, is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clean_name,
                clean_email,
                clean_phone,
                password_hash,
                clean_role,
                clean_service,
                clean_image_url,
                1 if is_active else 0,
            ),
        )
def set_user_active(user_id: int, is_active: bool) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET is_active = ? WHERE id = ?",
            (1 if is_active else 0, user_id),
        ) 
def delete_user(user_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,),
        )               
# -------------------------
# SHIFTS
# -------------------------

def list_working_agent_ids(shift_date: str) -> set[int]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT agent_id FROM shifts WHERE shift_date = ?",
            (shift_date,),
        ).fetchall()
        return {int(r["agent_id"]) for r in rows}


def set_working_agents_for_date(shift_date: str, agent_ids: List[int]) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM shifts WHERE shift_date = ?", (shift_date,))
        for aid in agent_ids:
            conn.execute(
                "INSERT OR IGNORE INTO shifts (shift_date, agent_id) VALUES (?, ?)",
                (shift_date, int(aid)),
            )


def list_working_agents_for_date(shift_date: str) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT a.id, a.name, a.phone, a.whatsapp_optin, a.is_active
            FROM shifts s
            JOIN agents a ON a.id = s.agent_id
            WHERE s.shift_date = ?
              AND a.is_active = 1
            ORDER BY a.name COLLATE NOCASE
            """,
            (shift_date,),
        ).fetchall()

        return [
            {
                "id": r["id"],
                "name": r["name"],
                "phone": r["phone"],
                "whatsapp_optin": bool(r["whatsapp_optin"]),
                "is_active": bool(r["is_active"]),
            }
            for r in rows
        ]





# -------------------------
# FOODS
# -------------------------

def add_food(name: str, unit: str = "unit") -> None:
    clean_name = name.strip()
    clean_unit = (unit or "unit").strip()

    if not clean_name:
        return

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO foods (name, unit, is_active)
            VALUES (?, ?, 1)
            ON CONFLICT(name) DO UPDATE SET is_active = 1
            """,
            (clean_name, clean_unit),
        )


def list_foods(active_only: bool = True) -> list[dict]:
    with get_conn() as conn:
        if active_only:
            rows = conn.execute(
                "SELECT id, name, unit, is_active FROM foods WHERE is_active = 1 ORDER BY name"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, name, unit, is_active FROM foods ORDER BY name"
            ).fetchall()

    return [
        {"id": r["id"], "name": r["name"], "unit": r["unit"], "is_active": r["is_active"]}
        for r in rows
    ]


def set_food_active(food_id: int, is_active: bool) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE foods SET is_active = ? WHERE id = ?",
            (1 if is_active else 0, food_id),
        )


# -------------------------
# RECIPES
# -------------------------

def add_recipe(name: str) -> None:
    clean_name = name.strip()
    if not clean_name:
        return

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO recipes (name, is_active)
            VALUES (?, 1)
            ON CONFLICT(name) DO UPDATE SET is_active = 1
            """,
            (clean_name,),
        )


def list_recipes(active_only: bool = True) -> list[dict]:
    with get_conn() as conn:
        if active_only:
            rows = conn.execute(
                "SELECT id, name, is_active FROM recipes WHERE is_active = 1 ORDER BY name"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, name, is_active FROM recipes ORDER BY name"
            ).fetchall()

    return [
        {"id": r["id"], "name": r["name"], "is_active": r["is_active"]}
        for r in rows
    ]


def set_recipe_active(recipe_id: int, is_active: bool) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE recipes SET is_active = ? WHERE id = ?",
            (1 if is_active else 0, recipe_id),
        )


# -------------------------
# OFFERS
# -------------------------

def list_offers_for_date(offer_date: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
              o.id, o.offer_date, o.offer_type, o.recipe_id, o.food_id,
              o.max_per_person, o.is_active,
              r.name AS recipe_name,
              f.name AS food_name,
              f.unit AS food_unit
            FROM offers o
            LEFT JOIN recipes r ON r.id = o.recipe_id
            LEFT JOIN foods f ON f.id = o.food_id
            WHERE o.offer_date = ?
            ORDER BY o.offer_type DESC, COALESCE(r.name, f.name)
            """,
            (offer_date,),
        ).fetchall()

    out = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "offer_date": r["offer_date"],
                "offer_type": r["offer_type"],
                "recipe_id": r["recipe_id"],
                "food_id": r["food_id"],
                "max_per_person": r["max_per_person"],
                "is_active": r["is_active"],
                "label": r["recipe_name"] if r["offer_type"] == "MAIN" else r["food_name"],
                "unit": r["food_unit"] if r["offer_type"] == "SIDE" else None,
            }
        )
    return out


def add_offer_main(offer_date: str, recipe_id: int, max_per_person: int) -> None:
    m = int(max(1, max_per_person))
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id FROM offers
            WHERE offer_date = ? AND offer_type = 'MAIN' AND recipe_id = ?
            """,
            (offer_date, recipe_id),
        ).fetchone()

        if row:
            conn.execute(
                "UPDATE offers SET is_active = 1, max_per_person = ? WHERE id = ?",
                (m, row["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO offers (offer_date, offer_type, recipe_id, food_id, max_per_person, is_active)
                VALUES (?, 'MAIN', ?, NULL, ?, 1)
                """,
                (offer_date, recipe_id, m),
            )


def add_offer_side(offer_date: str, food_id: int, max_per_person: int) -> None:
    m = int(max(1, max_per_person))
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id FROM offers
            WHERE offer_date = ? AND offer_type = 'SIDE' AND food_id = ?
            """,
            (offer_date, food_id),
        ).fetchone()

        if row:
            conn.execute(
                "UPDATE offers SET is_active = 1, max_per_person = ? WHERE id = ?",
                (m, row["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO offers (offer_date, offer_type, recipe_id, food_id, max_per_person, is_active)
                VALUES (?, 'SIDE', NULL, ?, ?, 1)
                """,
                (offer_date, food_id, m),
            )


def update_offer_max(offer_id: int, max_per_person: int) -> None:
    m = int(max(1, max_per_person))
    with get_conn() as conn:
        conn.execute(
            "UPDATE offers SET max_per_person = ? WHERE id = ?",
            (m, offer_id),
        )


def set_offer_active(offer_id: int, is_active: bool) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE offers SET is_active = ? WHERE id = ?",
            (1 if is_active else 0, offer_id),
        )


# -------------------------
# RESERVATIONS (new lines)
# -------------------------

def create_reservation(event_id: int, name: str, bring: str) -> int:
    clean_name = name.strip()
    clean_bring = (bring or "").strip()

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO reservations (event_id, name, items_json, bring)
            VALUES (?, ?, '[]', ?)
            """,
            (event_id, clean_name, clean_bring),
        )
        return int(cur.lastrowid)


def set_reservation_lines(reservation_id: int, lines: list[tuple[int, int]]) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM reservation_lines WHERE reservation_id = ?", (reservation_id,))
        conn.executemany(
            "INSERT INTO reservation_lines (reservation_id, offer_id, qty) VALUES (?, ?, ?)",
            [(reservation_id, offer_id, qty) for offer_id, qty in lines],
        )


def list_active_offers_for_date(offer_date: str) -> dict:
    offers = list_offers_for_date(offer_date)
    active = [o for o in offers if o["is_active"]]
    mains = [o for o in active if o["offer_type"] == "MAIN"]
    sides = [o for o in active if o["offer_type"] == "SIDE"]
    return {"mains": mains, "sides": sides}


def list_reservations_with_lines(event_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT
              r.id AS reservation_id,
              r.name,
              r.bring,
              rl.qty,
              o.offer_type,
              COALESCE(rec.name, f.name) AS label
            FROM reservations r
            LEFT JOIN reservation_lines rl ON rl.reservation_id = r.id
            LEFT JOIN offers o ON o.id = rl.offer_id
            LEFT JOIN recipes rec ON rec.id = o.recipe_id
            LEFT JOIN foods f ON f.id = o.food_id
            WHERE r.event_id = ?
            ORDER BY r.id DESC
            """,
            (event_id,),
        ).fetchall()

    out: list[dict] = []
    by_id: dict[int, dict] = {}

    for row in rows:
        rid = row["reservation_id"]
        if rid not in by_id:
            by_id[rid] = {"name": row["name"], "bring": row["bring"] or "", "lines": []}
            out.append(by_id[rid])

        if row["label"] is not None and row["qty"] is not None:
            by_id[rid]["lines"].append({"label": row["label"], "qty": int(row["qty"]), "type": row["offer_type"]})

    return out


def reservation_exists_for_event(event_id: int, name: str) -> bool:
    name_norm = name.strip().lower()
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT 1
            FROM reservations
            WHERE event_id = ?
              AND lower(trim(name)) = ?
            LIMIT 1
            """,
            (event_id, name_norm),
        ).fetchone()
        return row is not None

def get_recipe(recipe_id: int) -> dict | None:
    with get_conn() as conn:
        r = conn.execute(
            "SELECT id, name, is_active FROM recipes WHERE id = ?",
            (recipe_id,),
        ).fetchone()
        if not r:
            return None
        return {"id": r["id"], "name": r["name"], "is_active": bool(r["is_active"])}
def get_tomorrow_admin_snapshot(event_date: str) -> dict:
    """
    Snapshot "cockpit admin" pour une date donnée (en pratique : demain).
    Centralise les données utiles au dashboard admin.
    """
    event = get_event(event_date)

    offers = list_active_offers_for_date(event_date)
    mains = offers.get("mains", [])
    sides = offers.get("sides", [])

    working_agents = list_working_agents_for_date(event_date)

    reservations = []
    if event:
        reservations = list_reservations_with_lines(event["id"])

    total_reservations = len(reservations)

    totals_main: dict[str, int] = {}
    totals_side: dict[str, int] = {}
    brings: list[str] = []

    for r in reservations:
        bring = (r.get("bring") or "").strip()
        if bring:
            brings.append(bring)

        for line in (r.get("lines") or []):
            label = line.get("label") or "?"
            qty = int(line.get("qty") or 0)
            line_type = line.get("type")

            if qty <= 0:
                continue

            if line_type == "MAIN":
                totals_main[label] = totals_main.get(label, 0) + qty
            else:
                totals_side[label] = totals_side.get(label, 0) + qty

    snapshot = {
        "event": event,
        "offers": {
            "mains": mains,
            "sides": sides,
        },
        "working_agents": working_agents,
        "reservations": reservations,
        "kpis": {
            "reservations_count": total_reservations,
            "working_agents_count": len(working_agents),
            "mains_count": len(mains),
            "sides_count": len(sides),
        },
        "totals": {
            "mains": totals_main,
            "sides": totals_side,
        },
        "brings": brings,
    }

    return snapshot

def update_recipe(recipe_id: int, name: str, is_active: bool) -> None:
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Recipe name is required")

    with get_conn() as conn:
        conn.execute(
            """
            UPDATE recipes
            SET name = ?, is_active = ?
            WHERE id = ?
            """,
            (clean_name, 1 if is_active else 0, recipe_id),
        )
def update_event_flags(event_date: str, open_value: int = None, is_planned_value: int = None) -> None:
    fields = []
    values = []

    if open_value is not None:
        fields.append("is_open = ?")
        values.append(int(open_value))

    if is_planned_value is not None:
        fields.append("is_planned = ?")
        values.append(int(is_planned_value))

    if not fields:
        return

    values.append(event_date)

    query = f"""
        UPDATE events
        SET {", ".join(fields)}
        WHERE event_date = ?
    """

    with get_conn() as conn:
        conn.execute(query, values)

def delete_offer(offer_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM offers WHERE id = ?",
            (offer_id,),
        )
        
def update_user(
    user_id: int,
    name: str,
    email: str,
    phone: str,
    role: str,
    service: str,
    image_url: str | None,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE users
            SET name = ?, email = ?, phone = ?, role = ?, service = ?, image_url = ?
            WHERE id = ?
            """,
            (name, email, phone, role, service, image_url, user_id),
        )   

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    clean_email = email.strip().lower()

    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id, name, email, phone, password_hash, role, service, image_url, is_active, created_at
            FROM users
            WHERE lower(trim(email)) = ?
            LIMIT 1
            """,
            (clean_email,),
        ).fetchone()

        if not row:
            return None

        return {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "phone": row["phone"],
            "password_hash": row["password_hash"],
            "role": row["role"],
            "service": row["service"],
            "image_url": row["image_url"],
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
        }

def authenticate_user(email: str, password_hash: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_email(email)

    if not user:
        return None

    if not user["is_active"]:
        return None

    if user["password_hash"] != password_hash:
        return None

    return user             

def delete_reservation_for_event_and_name(event_id: int, name: str) -> None:
    clean_name = name.strip().lower()

    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT id
            FROM reservations
            WHERE event_id = ?
              AND lower(trim(name)) = ?
            LIMIT 1
            """,
            (event_id, clean_name),
        ).fetchone()

        if not row:
            return

        reservation_id = int(row["id"])

        conn.execute(
            "DELETE FROM reservation_lines WHERE reservation_id = ?",
            (reservation_id,),
        )
        conn.execute(
            "DELETE FROM reservations WHERE id = ?",
            (reservation_id,),
        )

def set_event_breakfast_price(event_date: str, breakfast_price: float) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE events
            SET breakfast_price = ?
            WHERE event_date = ?
            """,
            (float(breakfast_price), event_date),
        )