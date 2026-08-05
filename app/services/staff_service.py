from app.database.db import get_db


class StaffService:
    def __init__(self):
        self._db = get_db()

    def list_all(self):
        return self._db.fetchall("SELECT * FROM staff ORDER BY is_active DESC, name")

    def list_active(self):
        return self._db.fetchall("SELECT * FROM staff WHERE is_active=1 ORDER BY name")

    def list_waiters(self):
        return self._db.fetchall(
            "SELECT * FROM staff WHERE is_active=1 AND role != 'Rider' ORDER BY name"
        )

    def list_riders(self):
        return self._db.fetchall(
            "SELECT * FROM staff WHERE is_active=1 AND role='Rider' ORDER BY name"
        )

    def add(self, name, role, phone=""):
        self._db.execute(
            "INSERT INTO staff (name, role, phone) VALUES (?,?,?)", (name, role, phone)
        )

    def update(self, staff_id, name, role, phone, is_active=True):
        self._db.execute(
            "UPDATE staff SET name=?, role=?, phone=?, is_active=? WHERE id=?",
            (name, role, phone, 1 if is_active else 0, staff_id),
        )

    def delete(self, staff_id):
        self._db.execute("DELETE FROM staff WHERE id=?", (staff_id,))


staff_service = StaffService()
