import datetime
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from app.config import DB_PATH
from app.ui.theme import apply_theme
from app.utils.crash_guard import install, get_logger

log = get_logger()


def check_database():
    from app.database.db import get_db
    db = get_db()
    tables = {r["name"] for r in db.fetchall(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    required = {
        "users", "settings", "categories", "products", "tables", "staff",
        "orders", "order_items", "expenses", "expense_categories",
    }
    missing = required - tables
    if missing:
        raise RuntimeError(f"Database is missing tables: {', '.join(sorted(missing))}")
    log.info("Database OK: %s", DB_PATH)


def auto_backup():
    backup_dir = DB_PATH.parent / "backups"
    if not backup_dir.exists():
        return
    latest = None
    for f in sorted(backup_dir.glob("openpos_backup_*.db")):
        latest = f
    if latest is None or datetime.datetime.fromtimestamp(latest.stat().st_mtime) < datetime.datetime.now() - datetime.timedelta(hours=24):
        try:
            from app.database.db import get_db
            path = get_db().backup()
            print(f"Auto backup created: {path}")
        except Exception as e:
            print(f"Backup failed: {e}")


def main():
    install()
    app = QApplication(sys.argv)
    app.setApplicationName("Open POS")
    apply_theme(app)

    try:
        check_database()
    except Exception as e:
        log.exception("Database startup check failed")
        QMessageBox.critical(
            None,
            "Database Error",
            f"Could not open the database:\n\n{e}\n\n"
            f"Path: {DB_PATH}\n\nPlease restore a backup and try again.",
        )
        return 1

    auto_backup()

    from app.services.settings_service import settings_service
    settings_service.store_logo_path()

    from app.ui.login_view import LoginDialog
    from app.ui.main_window import MainWindow

    while True:
        login = LoginDialog()
        if login.exec() != LoginDialog.Accepted:
            app.quit()
            return 0
        user = login.current_user()
        window = MainWindow(user)
        window.show()

        logged_out = [False]

        def _on_logout():
            logged_out[0] = True
            window.close()

        window.logout_requested.connect(_on_logout)
        app.exec()
        if not logged_out[0]:
            break

    return 0


if __name__ == "__main__":
    sys.exit(main())
