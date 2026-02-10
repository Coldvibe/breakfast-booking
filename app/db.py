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
