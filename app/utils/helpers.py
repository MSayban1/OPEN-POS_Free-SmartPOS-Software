import hashlib
import os
import secrets
from datetime import datetime


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return dk.hex(), salt


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    dk, _ = hash_password(password, salt)
    return secrets.compare_digest(dk, password_hash)


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def fmt_money(value: float, currency: str = "Rs") -> str:
    try:
        value = float(value or 0)
    except (TypeError, ValueError):
        value = 0.0
    sign = "-" if value < 0 else ""
    return f"{sign}{currency} {abs(value):,.2f}"


def fmt_date(iso: str) -> str:
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d-%b-%Y")
    except Exception:
        return iso or ""


def fmt_datetime(iso: str) -> str:
    try:
        return datetime.strptime(iso, "%Y-%m-%d %H:%M:%S").strftime("%d-%b-%Y %I:%M %p")
    except Exception:
        return iso or ""


def day_name(iso: str) -> str:
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%A")
    except Exception:
        return ""


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path
