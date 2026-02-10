import hashlib
import hmac
import os
from typing import Optional

from fastapi import Request
from fastapi.responses import RedirectResponse


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def verify_password(plain: str, expected_plain: str) -> bool:
    # On compare en constant-time (anti timing attacks)
    return hmac.compare_digest(plain.encode("utf-8"), expected_plain.encode("utf-8"))


def is_admin_logged_in(request: Request) -> bool:
    return bool(request.session.get("admin") is True)


def require_admin(request: Request):
    if not is_admin_logged_in(request):
        # redirect login
        return RedirectResponse("/admin/login", status_code=303)
    return None


def admin_credentials_ok(username: str, password: str) -> bool:
    admin_user = _env("ADMIN_USERNAME", "admin")
    admin_pass = _env("ADMIN_PASSWORD", "change-me")
    return (username == admin_user) and verify_password(password, admin_pass)
