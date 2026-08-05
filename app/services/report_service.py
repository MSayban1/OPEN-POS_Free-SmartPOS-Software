import calendar
from datetime import date, datetime, timedelta

from app.database.db import get_db
from app.services.expense_service import expense_service
from app.services.settings_service import settings_service


def _filter_where(filters):
    clauses = []
    params = []
    if filters.get("order_type"):
        clauses.append("o.order_type=?")
        params.append(filters["order_type"])
    if filters.get("payment_method"):
        clauses.append("o.payment_method=?")
        params.append(filters["payment_method"])
    if filters.get("waiter_id"):
        clauses.append("o.waiter_id=?")
        params.append(filters["waiter_id"])
    return (" AND " + " AND ".join(clauses)) if clauses else "", params


class ReportService:
    def __init__(self):
        self._db = get_db()

    def sales_between(self, start: str, end: str, **filters):
        where, params = _filter_where(filters)
        q = (
            "SELECT o.id, o.order_number, o.order_type, o.status, o.subtotal, o.discount, o.tax, "
            "o.service_charge, o.total, o.created_at, o.payment_method, t.table_no, w.name AS waiter_name, "
            "u.full_name AS cashier_name FROM orders o "
            "LEFT JOIN tables t ON t.id=o.table_id "
            "LEFT JOIN staff w ON w.id=o.waiter_id "
            "LEFT JOIN users u ON u.id=o.cashier_id "
            "WHERE o.status IN ('paid','closed') AND date(o.created_at) BETWEEN ? AND ?"
        )
        params = [start, end] + params
        q += where
        q += " ORDER BY o.created_at"
        return self._db.fetchall(q, params)

    def sales_totals_between(self, start, end, **filters):
        rows = self.sales_between(start, end, **filters)
        subtotal = sum(float(r["subtotal"]) for r in rows)
        discount = sum(float(r["discount"]) for r in rows)
        tax = sum(float(r["tax"]) for r in rows)
        service_charge = sum(float(r["service_charge"]) for r in rows)
        total = sum(float(r["total"]) for r in rows)
        count = len(rows)
        return {
            "subtotal": round(subtotal, 2),
            "discount": round(discount, 2),
            "tax": round(tax, 2),
            "service_charge": round(service_charge, 2),
            "total": round(total, 2),
            "count": count,
            "rows": rows,
        }

    def daily_series_between(self, start, end, **filters):
        where, params = _filter_where(filters)
        result = []
        s = date.fromisoformat(start)
        e = date.fromisoformat(end)
        d = s
        while d <= e:
            r = self._db.fetchone(
                "SELECT COALESCE(SUM(total),0) total, COUNT(*) c FROM orders o "
                "WHERE o.status IN ('paid','closed') AND date(o.created_at)=?"
                + where,
                [d.isoformat()] + params,
            )
            result.append(
                {
                    "date": d,
                    "label": d.strftime("%d %b"),
                    "total": float(r["total"]),
                    "count": r["c"],
                }
            )
            d += timedelta(days=1)
        return result

    def daily_series(self, days=7):
        today = date.today()
        start = (today - timedelta(days=days - 1)).isoformat()
        end = today.isoformat()
        return self.daily_series_between(start, end)

    def monthly_totals(self, year, month):
        start = f"{year:04d}-{month:02d}-01"
        last = calendar.monthrange(year, month)[1]
        end = f"{year:04d}-{month:02d}-{last:02d}"
        return self.sales_totals_between(start, end)

    def profit_loss(self, start, end, **filters):
        sales = self.sales_totals_between(start, end, **filters)
        where, params = _filter_where(filters)
        cost = self._db.fetchone(
            "SELECT COALESCE(SUM(COALESCE(p.cost,0)*oi.qty),0) c FROM order_items oi "
            "JOIN orders o ON o.id=oi.order_id "
            "LEFT JOIN products p ON p.id=oi.product_id "
            "WHERE o.status IN ('paid','closed') AND date(o.created_at) BETWEEN ? AND ?"
            + where,
            [start, end] + params,
        )["c"]
        expenses = expense_service.total_between(start, end)
        net_sales = round(sales["subtotal"] - sales["discount"] + sales["service_charge"], 2)
        gross = round(net_sales - float(cost), 2)
        net = round(gross - expenses, 2)
        return {
            **sales,
            "net_sales": net_sales,
            "cost": round(float(cost), 2),
            "gross_profit": gross,
            "expenses": expenses,
            "net_profit": net,
        }

    def product_rank(self, start, end, limit=10, **filters):
        where, params = _filter_where(filters)
        return self._db.fetchall(
            "SELECT oi.product_id, oi.name, SUM(oi.qty) qty, SUM(oi.price*oi.qty) revenue "
            "FROM order_items oi JOIN orders o ON o.id=oi.order_id "
            "WHERE o.status IN ('paid','closed') AND date(o.created_at) BETWEEN ? AND ?"
            + where +
            " GROUP BY oi.product_id, oi.name ORDER BY qty DESC LIMIT ?",
            [start, end] + params + [limit],
        )

    def waiter_rank(self, start, end):
        return self._db.fetchall(
            "SELECT COALESCE(w.name,'-') waiter, COUNT(o.id) orders, SUM(o.total) revenue "
            "FROM orders o LEFT JOIN staff w ON w.id=o.waiter_id "
            "WHERE o.status IN ('paid','closed') AND date(o.created_at) BETWEEN ? AND ? "
            "GROUP BY w.id ORDER BY revenue DESC",
            (start, end),
        )

    def payment_breakdown(self, start, end, **filters):
        where, params = _filter_where(filters)
        return self._db.fetchall(
            "SELECT COALESCE(payment_method,'-') method, COUNT(*) c, SUM(total) total FROM orders o "
            "WHERE o.status IN ('paid','closed') AND date(o.created_at) BETWEEN ? AND ?"
            + where +
            " GROUP BY payment_method ORDER BY total DESC",
            [start, end] + params,
        )

    def order_type_breakdown(self, start, end, **filters):
        f2 = dict(filters)
        f2.pop("order_type", None)
        where, params = _filter_where(f2)
        return self._db.fetchall(
            "SELECT order_type, COUNT(*) c, SUM(total) total FROM orders o "
            "WHERE o.status IN ('paid','closed') AND date(o.created_at) BETWEEN ? AND ?"
            + where +
            " GROUP BY order_type ORDER BY total DESC",
            [start, end] + params,
        )

    def category_sales(self, start, end, **filters):
        where, params = _filter_where(filters)
        return self._db.fetchall(
            "SELECT COALESCE(c.name,'Uncategorized') category, "
            "COALESCE(SUM(oi.price*oi.qty),0) revenue, COALESCE(SUM(oi.qty),0) qty "
            "FROM order_items oi "
            "JOIN orders o ON o.id=oi.order_id "
            "LEFT JOIN products p ON p.id=oi.product_id "
            "LEFT JOIN categories c ON c.id=p.category_id "
            "WHERE o.status IN ('paid','closed') AND date(o.created_at) BETWEEN ? AND ?"
            + where +
            " GROUP BY c.id ORDER BY revenue DESC",
            [start, end] + params,
        )

    def staff_performance(self, start, end, role="Waiter", **filters):
        if role == "Rider":
            return self._db.fetchall(
                "SELECT COALESCE(w.name,'-') name, COUNT(DISTINCT o.id) orders, "
                "COALESCE(SUM(o.total),0) revenue, COALESCE(AVG(o.total),0) avg_ticket "
                "FROM orders o LEFT JOIN staff w ON w.id=o.rider_id "
                "WHERE o.status IN ('paid','closed') AND date(o.created_at) BETWEEN ? AND ? "
                "GROUP BY w.id ORDER BY revenue DESC",
                (start, end),
            )
        f2 = dict(filters)
        f2.pop("waiter_id", None)
        where, params = _filter_where(f2)
        return self._db.fetchall(
            "SELECT COALESCE(w.name,'-') name, COUNT(DISTINCT o.id) orders, "
            "COALESCE(SUM(o.total),0) revenue, COALESCE(AVG(o.total),0) avg_ticket, "
            "COALESCE(SUM(oi.qty),0) items "
            "FROM orders o LEFT JOIN staff w ON w.id=o.waiter_id "
            "LEFT JOIN order_items oi ON oi.order_id=o.id "
            "WHERE o.status IN ('paid','closed') AND date(o.created_at) BETWEEN ? AND ?"
            + where +
            " GROUP BY w.id ORDER BY revenue DESC",
            [start, end] + params,
        )

    def list_payment_methods(self):
        return [r["method"] for r in self._db.fetchall(
            "SELECT DISTINCT payment_method method FROM orders WHERE payment_method IS NOT NULL"
        )]

    def list_waiters(self):
        return self._db.fetchall(
            "SELECT id, name FROM staff WHERE is_active=1 AND role='Waiter' ORDER BY name"
        )

    def today(self):
        d = date.today().isoformat()
        return self.sales_totals_between(d, d)

    def this_month(self):
        today = date.today()
        return self.monthly_totals(today.year, today.month)


report_service = ReportService()
