from app.database.db import get_db


class ProductService:
    def __init__(self):
        self._db = get_db()

    def list_categories(self):
        return self._db.fetchall("SELECT * FROM categories ORDER BY sort_order, name")

    def add_category(self, name):
        self._db.execute("INSERT INTO categories (name) VALUES (?)", (name,))

    def update_category(self, cat_id, name):
        self._db.execute("UPDATE categories SET name=? WHERE id=?", (name, cat_id))

    def delete_category(self, cat_id):
        products = self._db.fetchone(
            "SELECT COUNT(*) c FROM products WHERE category_id=?", (cat_id,)
        )
        if products and products["c"] > 0:
            raise ValueError("Category has products. Move or delete them first.")
        self._db.execute("DELETE FROM categories WHERE id=?", (cat_id,))

    def list_products(self, include_inactive=True):
        sql = (
            "SELECT p.*, c.name AS category_name FROM products p "
            "LEFT JOIN categories c ON c.id=p.category_id"
        )
        if not include_inactive:
            sql += " WHERE p.is_active=1"
        return self._db.fetchall(sql + " ORDER BY p.name")

    def list_active(self, search="", category_id=None):
        sql = (
            "SELECT p.*, c.name AS category_name FROM products p "
            "LEFT JOIN categories c ON c.id=p.category_id WHERE p.is_active=1"
        )
        params = []
        if search:
            sql += " AND p.name LIKE ?"
            params.append(f"%{search}%")
        if category_id:
            sql += " AND p.category_id=?"
            params.append(category_id)
        return self._db.fetchall(sql + " ORDER BY c.sort_order, p.name", params)

    def get(self, product_id):
        return self._db.fetchone("SELECT * FROM products WHERE id=?", (product_id,))

    def add(self, name, price, cost, category_id):
        self._db.execute(
            "INSERT INTO products (name, price, cost, category_id) VALUES (?,?,?,?)",
            (name, price, cost, category_id),
        )

    def update(self, product_id, name, price, cost, category_id, is_active=True):
        self._db.execute(
            "UPDATE products SET name=?, price=?, cost=?, category_id=?, is_active=? WHERE id=?",
            (name, price, cost, category_id, 1 if is_active else 0, product_id),
        )

    def delete(self, product_id):
        self._db.execute("DELETE FROM products WHERE id=?", (product_id,))


product_service = ProductService()
