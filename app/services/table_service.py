from app.database.db import get_db


class TableService:
    def __init__(self):
        self._db = get_db()

    def list_all(self):
        return self._db.fetchall(
            "SELECT t.*, o.waiter_id, w.name AS waiter_name, o.total AS current_total, "
            "o.created_at AS opened_at FROM tables t "
            "LEFT JOIN orders o ON o.id=t.current_order_id "
            "LEFT JOIN staff w ON w.id=o.waiter_id ORDER BY CAST(t.table_no AS INTEGER), t.table_no"
        )

    def add(self, table_no, seats):
        if self._db.fetchone("SELECT id FROM tables WHERE table_no=?", (table_no,)):
            raise ValueError("Table number already exists.")
        self._db.execute(
            "INSERT INTO tables (table_no, seats) VALUES (?,?)", (table_no, seats)
        )

    def update(self, table_id, table_no, seats):
        row = self._db.fetchone(
            "SELECT id FROM tables WHERE table_no=? AND id!=?", (table_no, table_id)
        )
        if row:
            raise ValueError("Table number already exists.")
        self._db.execute(
            "UPDATE tables SET table_no=?, seats=? WHERE id=?", (table_no, seats, table_id)
        )

    def delete(self, table_id):
        row = self._db.fetchone("SELECT status FROM tables WHERE id=?", (table_id,))
        if row and row["status"] != "free":
            raise ValueError("Occupied tables cannot be deleted.")
        self._db.execute("DELETE FROM tables WHERE id=?", (table_id,))

    def get(self, table_id):
        return self._db.fetchone("SELECT * FROM tables WHERE id=?", (table_id,))

    def set_status(self, table_id, status, order_id=None):
        self._db.execute(
            "UPDATE tables SET status=?, current_order_id=? WHERE id=?",
            (status, order_id, table_id),
        )

    def count_by_status(self):
        return {
            r["status"]: r["c"]
            for r in self._db.fetchall("SELECT status, COUNT(*) c FROM tables GROUP BY status")
        }


table_service = TableService()
