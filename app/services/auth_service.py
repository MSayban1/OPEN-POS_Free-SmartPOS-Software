from app.database.db import get_db
from app.utils.helpers import hash_password, verify_password


class AuthService:
    def __init__(self):
        self._db = get_db()
        self.current_user = None

    def login(self, username: str, password: str) -> tuple[bool, str, dict | None]:
        if not username.strip() or not password:
            return False, "Enter username and password.", None
        user = self._db.fetchone("SELECT * FROM users WHERE username=?", (username.strip(),))
        if not user:
            return False, "Invalid username or password.", None
        if not user["is_active"]:
            return False, "Account is disabled. Contact admin.", None
        if not verify_password(password, user["salt"], user["password_hash"]):
            return False, "Invalid username or password.", None
        self.current_user = dict(user)
        return True, "Success", dict(user)

    def logout(self):
        self.current_user = None

    def list_users(self):
        return self._db.fetchall("SELECT * FROM users ORDER BY id")

    def add_user(self, username, password, full_name, role):
        if self._db.fetchone("SELECT id FROM users WHERE username=?", (username,)):
            raise ValueError("Username already exists.")
        h, salt = hash_password(password)
        self._db.execute(
            "INSERT INTO users (username, password_hash, salt, full_name, role) VALUES (?,?,?,?,?)",
            (username, h, salt, full_name, role),
        )

    def update_user(self, user_id, full_name, role, is_active):
        self._db.execute(
            "UPDATE users SET full_name=?, role=?, is_active=? WHERE id=?",
            (full_name, role, 1 if is_active else 0, user_id),
        )

    def set_password(self, user_id, password):
        h, salt = hash_password(password)
        self._db.execute(
            "UPDATE users SET password_hash=?, salt=? WHERE id=?", (h, salt, user_id)
        )

    def delete_user(self, user_id):
        self._db.execute("DELETE FROM users WHERE id=? AND role!='admin'", (user_id,))


auth_service = AuthService()
