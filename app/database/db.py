import shutil
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from app.config import DB_PATH
from app.utils.helpers import hash_password

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin','manager','cashier')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    price REAL NOT NULL DEFAULT 0,
    cost REAL NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_no TEXT UNIQUE NOT NULL,
    seats INTEGER NOT NULL DEFAULT 2,
    status TEXT NOT NULL DEFAULT 'free',
    current_order_id INTEGER
);

CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'Waiter',
    phone TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE NOT NULL,
    order_type TEXT NOT NULL DEFAULT 'dine-in',
    table_id INTEGER,
    waiter_id INTEGER,
    rider_id INTEGER,
    cashier_id INTEGER,
    status TEXT NOT NULL DEFAULT 'open',
    subtotal REAL NOT NULL DEFAULT 0,
    discount REAL NOT NULL DEFAULT 0,
    discount_type TEXT NOT NULL DEFAULT 'amount',
    service_charge REAL NOT NULL DEFAULT 0,
    tax REAL NOT NULL DEFAULT 0,
    total REAL NOT NULL DEFAULT 0,
    instructions TEXT NOT NULL DEFAULT '',
    customer_name TEXT NOT NULL DEFAULT '',
    customer_phone TEXT NOT NULL DEFAULT '',
    customer_address TEXT NOT NULL DEFAULT '',
    payment_method TEXT NOT NULL DEFAULT 'Cash',
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    closed_at TEXT
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER,
    name TEXT NOT NULL,
    price REAL NOT NULL DEFAULT 0,
    qty REAL NOT NULL DEFAULT 1,
    instructions TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS expense_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER REFERENCES expense_categories(id) ON DELETE SET NULL,
    category_name TEXT,
    description TEXT NOT NULL DEFAULT '',
    amount REAL NOT NULL DEFAULT 0,
    expense_date TEXT NOT NULL DEFAULT (date('now','localtime')),
    created_by INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(expense_date);
"""

_DEFAULT_SETTINGS = {
    "store_name": "Open POS",
    "store_logo": "",
    "store_email": "saban.productions00@gmail.com",
    "store_phone": "0300-1234567",
    "store_address": "Main Boulevard, Lahore",
    "currency": "Rs",
    "tax_name": "Sales Tax",
    "tax_rate": "16",
    "receipt_footer": "Thank you for visiting!",
    "receipt_show_logo": "1",
    "receipt_show_address": "1",
    "delivery_charge": "0",
    "takeaway_charge": "0",
    "tax_dinein": "1",
    "tax_takeaway": "1",
    "tax_delivery": "1",
    "next_order_number": "1000",
    "printer_name": "",
    "printer_encoding": "cp437",
    "printer_cols": "42",
    "printer_cut": "1",
}


class Database:
    _instance = None
    _lock = threading.RLock()

    def __init__(self, path: Path | None = None):
        self._conn = sqlite3.connect(str(path or DB_PATH), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._tls = threading.local()

    @classmethod
    def get(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
                cls._instance.init_schema()
                cls._instance.seed()
            return cls._instance

    @contextmanager
    def cursor(self):
        with self._lock:
            cur = self._conn.cursor()
            try:
                yield cur
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
            finally:
                cur.close()

    def fetchall(self, sql, params=()):
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    def fetchone(self, sql, params=()):
        with self._lock:
            return self._conn.execute(sql, params).fetchone()

    def execute(self, sql, params=()):
        with self._lock:
            cur = self._conn.execute(sql, params)
            self._conn.commit()
            return cur.lastrowid

    def executemany(self, sql, seq):
        with self._lock:
            self._conn.executemany(sql, seq)
            self._conn.commit()

    def init_schema(self):
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        self._migrate()

    def _migrate(self):
        cols = {r["name"] for r in self._conn.execute("PRAGMA table_info(orders)").fetchall()}
        for name, ddl in {
            "customer_name": "TEXT NOT NULL DEFAULT ''",
            "customer_phone": "TEXT NOT NULL DEFAULT ''",
            "customer_address": "TEXT NOT NULL DEFAULT ''",
            "service_charge": "REAL NOT NULL DEFAULT 0",
            "rider_id": "INTEGER",
        }.items():
            if name not in cols:
                self._conn.execute(f"ALTER TABLE orders ADD COLUMN {name} {ddl}")
        pcols = {r["name"] for r in self._conn.execute("PRAGMA table_info(products)").fetchall()}
        for name in ("stock", "barcode"):
            if name in pcols:
                self._conn.execute(f"ALTER TABLE products DROP COLUMN {name}")
        self._conn.execute("DELETE FROM settings WHERE key='tax_categories'")
        self._conn.commit()

    def seed(self):
        if not self.fetchone("SELECT id FROM users LIMIT 1"):
            h, salt = hash_password("admin123")
            self.execute(
                "INSERT INTO users (username, password_hash, salt, full_name, role) VALUES (?,?,?,?,?)",
                ("admin", h, salt, "Administrator", "admin"),
            )
        existing = {r["key"] for r in self.fetchall("SELECT key FROM settings")}
        for k, v in _DEFAULT_SETTINGS.items():
            if k not in existing:
                self.execute("INSERT INTO settings (key, value) VALUES (?,?)", (k, v))

        if not self.fetchone("SELECT id FROM categories LIMIT 1"):
            seed_categories = ["Coffee", "Tea", "Cold Drinks", "Shakes", "Desserts", "Snacks"]
            for i, name in enumerate(seed_categories, 1):
                self.execute(
                    "INSERT INTO categories (name, sort_order) VALUES (?,?)", (name, i)
                )
            products = [
                ("Espresso", 250, 90, 1),
                ("Cappuccino", 350, 140, 1),
                ("Latte", 380, 150, 1),
                ("Hot Chocolate", 400, 180, 1),
                ("Karak Chai", 150, 60, 2),
                ("Green Tea", 200, 80, 2),
                ("Iced Tea", 250, 100, 3),
                ("Cold Coffee", 350, 150, 3),
                ("Chocolate Shake", 450, 200, 4),
                ("Mango Shake", 420, 180, 4),
                ("Cheesecake Slice", 550, 300, 5),
                ("Brownie", 450, 200, 5),
                ("Sandwich", 400, 220, 6),
                ("Fries", 300, 120, 6),
                ("Club Sandwich", 550, 300, 6),
            ]
            for name, price, cost, cat in products:
                self.execute(
                    "INSERT INTO products (name, price, cost, category_id) VALUES (?,?,?,?)",
                    (name, price, cost, cat),
                )

        if not self.fetchone("SELECT id FROM staff LIMIT 1"):
            self.execute("INSERT INTO staff (name, role) VALUES (?,?)", ("Waiter 1", "Waiter"))
            self.execute("INSERT INTO staff (name, role) VALUES (?,?)", ("Waiter 2", "Waiter"))

        if not self.fetchone("SELECT id FROM tables LIMIT 1"):
            for i in range(1, 9):
                self.execute(
                    "INSERT INTO tables (table_no, seats) VALUES (?,?)", (f"T{i}", 2 if i % 2 else 4)
                )

        if not self.fetchone("SELECT id FROM expense_categories LIMIT 1"):
            for name in ("Rent", "Utilities", "Groceries", "Staff Salary", "Misc"):
                self.execute("INSERT INTO expense_categories (name) VALUES (?)", (name,))

    def close(self):
        with self._lock:
            try:
                self._conn.close()
            except Exception:
                pass

    def backup(self):
        import datetime

        backup_dir = DB_PATH.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = backup_dir / f"openpos_backup_{stamp}.db"
        return self.backup_to(dest)

    def backup_to(self, dest):
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("VACUUM INTO ?", (str(dest),))
        return dest

    @staticmethod
    def _validate_backup(path: Path):
        required = {
            "users", "settings", "categories", "products", "tables", "staff",
            "orders", "order_items", "expenses", "expense_categories",
        }
        conn = sqlite3.connect(str(path))
        try:
            conn.row_factory = sqlite3.Row
            tables = {r["name"] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            if not required.issubset(tables):
                raise ValueError(
                    "This file is not a valid Open POS backup (missing tables).")
            row = conn.execute("PRAGMA integrity_check").fetchone()
            if row and row["integrity_check"] != "ok":
                raise ValueError("Backup file failed the integrity check.")
        finally:
            conn.close()

    @classmethod
    def restore_from(cls, path: Path) -> "Database":
        path = Path(path)
        if not path.exists():
            raise ValueError("Backup file does not exist.")
        with cls._lock:
            cls._validate_backup(path)
            if cls._instance is not None:
                cls._instance.close()
            shutil.copyfile(path, DB_PATH)
            for suffix in ("-wal", "-shm"):
                extra = Path(str(DB_PATH) + suffix)
                if extra.exists():
                    try:
                        extra.unlink()
                    except OSError:
                        pass
            new = cls()
            new.init_schema()
            new.seed()
            cls._instance = new
            global db
            db = new
            rebind_services(new)
            return new

    @classmethod
    def reset_all(cls) -> "Database":
        with cls._lock:
            if cls._instance is not None:
                cls._instance.close()
            for p in (DB_PATH, Path(str(DB_PATH) + "-wal"), Path(str(DB_PATH) + "-shm")):
                if p.exists():
                    try:
                        p.unlink()
                    except OSError:
                        pass
            new = cls()
            new.init_schema()
            new.seed()
            cls._instance = new
            global db
            db = new
            rebind_services(new)
            return new


db = None


def get_db() -> Database:
    global db
    if db is None:
        db = Database.get()
    return db


def rebind_services(database: Database):
    """Re-point every service singleton's connection after a restore/reset."""
    from app.services import (
        auth_service, expense_service, order_service, product_service,
        report_service, settings_service, staff_service, table_service,
    )
    for mod in (auth_service, expense_service, order_service, product_service,
                report_service, settings_service, staff_service, table_service):
        singleton = getattr(mod, mod.__name__.rsplit(".", 1)[-1], None)
        if singleton is not None and hasattr(singleton, "_db"):
            singleton._db = database
    if hasattr(settings_service, "store_logo_path"):
        try:
            settings_service.store_logo_path()
        except Exception:
            pass

