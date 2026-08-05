from app.database.db import get_db


class ExpenseService:
    def __init__(self):
        self._db = get_db()

    def list_categories(self):
        return self._db.fetchall("SELECT * FROM expense_categories ORDER BY name")

    def add_category(self, name):
        self._db.execute("INSERT INTO expense_categories (name) VALUES (?)", (name,))

    def delete_category(self, cat_id):
        self._db.execute("DELETE FROM expense_categories WHERE id=?", (cat_id,))

    def add(self, category_id, description, amount, expense_date, created_by=None):
        category_name = None
        if category_id:
            cat = self._db.fetchone("SELECT name FROM expense_categories WHERE id=?", (category_id,))
            category_name = cat["name"] if cat else None
        self._db.execute(
            "INSERT INTO expenses (category_id, category_name, description, amount, expense_date, created_by) "
            "VALUES (?,?,?,?,?,?)",
            (category_id, category_name, description, amount, expense_date, created_by),
        )

    def delete(self, expense_id):
        self._db.execute("DELETE FROM expenses WHERE id=?", (expense_id,))

    def list(self, start=None, end=None):
        sql = "SELECT e.*, c.name AS cat FROM expenses e LEFT JOIN expense_categories c ON c.id=e.category_id"
        params = []
        if start:
            sql += " WHERE e.expense_date>=?"
            params.append(start)
        if end:
            sql += " AND e.expense_date<=?" if start else " WHERE e.expense_date<=?"
            params.append(end)
        return self._db.fetchall(sql + " ORDER BY e.expense_date DESC, e.id DESC", params)

    def total_between(self, start, end):
        r = self._db.fetchone(
            "SELECT COALESCE(SUM(amount),0) t FROM expenses WHERE expense_date BETWEEN ? AND ?",
            (start, end),
        )
        return float(r["t"]) if r else 0.0

    def by_category_between(self, start, end):
        return self._db.fetchall(
            "SELECT COALESCE(e.category_name,'Other') name, SUM(e.amount) total FROM expenses e "
            "WHERE e.expense_date BETWEEN ? AND ? GROUP BY e.category_name ORDER BY total DESC",
            (start, end),
        )


expense_service = ExpenseService()
