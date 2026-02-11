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
            CREATE TABLE IF NOT EXISTS weekly_menus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start TEXT NOT NULL UNIQUE, -- lundi (YYYY-MM-DD)
                menu_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                is_active INTEGER NOT NULL DEFAULT 1
            );
            """
        )
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








def ensure_event_for_date(event_date: str, default_menu: List[str]) -> None:
    """Crée l'event si absent."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM events WHERE event_date = ?",
            (event_date,),
        ).fetchone()
        if row:
            return
        conn.execute(
            "INSERT INTO events (event_date, menu_json, is_open) VALUES (?, ?, 1)",
            (event_date, json.dumps(default_menu, ensure_ascii=False)),
        )


def get_event(event_date: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, event_date, menu_json, is_open FROM events WHERE event_date = ?",
            (event_date,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "date": row["event_date"],
            "menu": json.loads(row["menu_json"]),
            "open": bool(row["is_open"]),
        }


def toggle_event_open(event_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE events SET is_open = CASE is_open WHEN 1 THEN 0 ELSE 1 END WHERE id = ?",
            (event_id,),
        )


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

def list_working_agent_ids(shift_date: str) -> set[int]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT agent_id FROM shifts WHERE shift_date = ?",
            (shift_date,),
        ).fetchall()
        return {int(r["agent_id"]) for r in rows}


def set_working_agents_for_date(shift_date: str, agent_ids: List[int]) -> None:
    # on remplace la liste complète pour la date
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
def get_weekly_menu(week_start: str) -> Optional[Dict[str, Any]]:
    import json
    with get_conn() as conn:
        row = conn.execute(
            "SELECT week_start, menu_json FROM weekly_menus WHERE week_start = ?",
            (week_start,),
        ).fetchone()
        if not row:
            return None
        return {
            "week_start": row["week_start"],
            "menu": json.loads(row["menu_json"]),
        }


def upsert_weekly_menu(week_start: str, menu: Dict[str, Any]) -> None:
    import json
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO weekly_menus (week_start, menu_json)
            VALUES (?, ?)
            ON CONFLICT(week_start) DO UPDATE SET menu_json = excluded.menu_json
            """,
            (week_start, json.dumps(menu, ensure_ascii=False)),
        )
def upsert_event_menu_preserve_open(event_date: str, menu: list[str]) -> None:
    import json
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, is_open FROM events WHERE event_date = ?",
            (event_date,),
        ).fetchone()

        menu_json = json.dumps(menu, ensure_ascii=False)

        if row:
            # on met à jour le menu, mais on garde is_open tel quel
            conn.execute(
                "UPDATE events SET menu_json = ? WHERE event_date = ?",
                (menu_json, event_date),
            )
        else:
            conn.execute(
                "INSERT INTO events (event_date, menu_json, is_open) VALUES (?, ?, 1)",
                (event_date, menu_json),
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
        # évite doublons : si déjà, on réactive + update max
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
