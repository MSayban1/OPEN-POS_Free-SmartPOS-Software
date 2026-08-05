from app.config import LOGOS_DIR
from app.database.db import get_db


class SettingsService:
    def __init__(self):
        self._db = get_db()

    def get_all(self) -> dict:
        return {r["key"]: r["value"] for r in self._db.fetchall("SELECT key, value FROM settings")}

    def get(self, key: str, default: str = "") -> str:
        r = self._db.fetchone("SELECT value FROM settings WHERE key=?", (key,))
        return r["value"] if r else default

    def set(self, key: str, value: str):
        self._db.execute(
            "INSERT INTO settings (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value)),
        )

    def set_many(self, items: dict):
        with self._db.cursor() as cur:
            for k, v in items.items():
                cur.execute(
                    "INSERT INTO settings (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (k, str(v)),
                )

    def get_float(self, key: str, default: float = 0.0) -> float:
        try:
            return float(self.get(key, str(default)))
        except (TypeError, ValueError):
            return default

    def next_order_number(self) -> str:
        with self._db.cursor() as cur:
            cur.execute("SELECT value FROM settings WHERE key='next_order_number'")
            row = cur.fetchone()
            try:
                n = int(row["value"]) if row else 1000
            except (TypeError, ValueError):
                n = 1000
            n += 1
            cur.execute(
                "INSERT INTO settings (key, value) VALUES ('next_order_number',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(n),),
            )
        return str(n)

    def store_logo_path(self):
        logo = self.get("store_logo", "").strip()
        if not logo:
            return None
        p = LOGOS_DIR / logo
        return str(p) if p.exists() else None


settings_service = SettingsService()
