import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.services.report_service import report_service
from app.services.settings_service import settings_service
from app.services.table_service import table_service
from app.ui.charts import BarChart
from app.ui.icons import icon_pixmap
from app.utils.helpers import fmt_money


def _stat_card(icon_name, label, value, color):
    card = QFrame()
    card.setProperty("card", True)
    card.setMinimumHeight(116)
    lay = QHBoxLayout(card)
    lay.setContentsMargins(18, 18, 18, 18)
    lay.setSpacing(16)
    icon_lbl = QLabel()
    icon_lbl.setPixmap(icon_pixmap(icon_name, color, 24))
    icon_lbl.setStyleSheet(f"background: {color}22; border-radius: 12px;")
    icon_lbl.setAlignment(Qt.AlignCenter)
    icon_lbl.setFixedSize(48, 48)
    lay.addWidget(icon_lbl)
    txt = QVBoxLayout()
    txt.setSpacing(2)
    val = QLabel(value)
    val.setObjectName("StatValue")
    txt.addWidget(val)
    lbl = QLabel(label)
    lbl.setObjectName("StatLabel")
    txt.addWidget(lbl)
    lay.addLayout(txt, 1)
    lay.addStretch()
    return card


class DashboardView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(16)

        title = QLabel("Dashboard")
        title.setObjectName("PageTitle")
        outer.addWidget(title)
        self.subtitle = QLabel("")
        self.subtitle.setObjectName("PageSubtitle")
        outer.addWidget(self.subtitle)

        cards = QHBoxLayout()
        cards.setSpacing(14)
        self.card_sales = _stat_card("coins", "Today's Sales", "Rs 0.00", "#4f46e5")
        self.card_orders = _stat_card("note", "Orders Today", "0", "#10b981")
        self.card_items = _stat_card("cup", "Items Sold", "0", "#f59e0b")
        self.card_tables = _stat_card("table", "Tables Busy", "0/0", "#ef4444")
        for c in (self.card_sales, self.card_orders, self.card_items, self.card_tables):
            cards.addWidget(c)
        outer.addLayout(cards)

        mid = QHBoxLayout()
        mid.setSpacing(14)
        chart_card = QFrame()
        chart_card.setProperty("card", True)
        cc = QVBoxLayout(chart_card)
        cc.setContentsMargins(16, 14, 16, 10)
        ctitle = QLabel("Last 7 Days Sales")
        ctitle.setObjectName("CardTitle")
        cc.addWidget(ctitle)
        self.chart = BarChart()
        cc.addWidget(self.chart)
        mid.addWidget(chart_card, 3)

        self.recent_card = QFrame()
        self.recent_card.setProperty("card", True)
        rc = QVBoxLayout(self.recent_card)
        rc.setContentsMargins(16, 14, 16, 10)
        rtitle = QLabel("Recent Orders")
        rtitle.setObjectName("CardTitle")
        rc.addWidget(rtitle)
        self.recent_table = QTableWidget(0, 4)
        self.recent_table.setHorizontalHeaderLabels(["Order", "Type", "Total", "Time"])
        self.recent_table.horizontalHeader().setStretchLastSection(True)
        self.recent_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setShowGrid(False)
        rc.addWidget(self.recent_table)
        mid.addWidget(self.recent_card, 2)
        outer.addLayout(mid, 1)

    def refresh(self):
        import datetime
        from app.utils.helpers import fmt_datetime

        settings = settings_service
        currency = settings.get("currency", "Rs")
        today = report_service.today()
        self.card_sales.findChildren(QLabel)[1].setText(fmt_money(today["total"], currency))
        self.card_orders.findChildren(QLabel)[1].setText(str(today["count"]))
        items = report_service._db.fetchone(
            "SELECT COALESCE(SUM(oi.qty),0) c FROM order_items oi "
            "JOIN orders o ON o.id=oi.order_id WHERE o.status IN ('paid','closed') "
            "AND date(o.created_at)=date('now','localtime')"
        )["c"]
        self.card_items.findChildren(QLabel)[1].setText(f"{int(items)}")
        status = table_service.count_by_status()
        total_tables = sum(status.values())
        busy = status.get("occupied", 0) + status.get("request_bill", 0)
        self.card_tables.findChildren(QLabel)[1].setText(f"{busy}/{total_tables}")

        today = datetime.date.today()
        self.chart.set_data([
            {"label": d["label"], "value": d["total"],
             "color": "#10b981" if d["date"] == today else "#4f46e5"}
            for d in report_service.daily_series(7)
        ])

        self.subtitle.setText(f"Overview for {today.strftime('%A, %d %B %Y')}")
        recent = report_service.sales_totals_between(
            datetime.date.today().isoformat(), datetime.date.today().isoformat()
        )["rows"]
        if not recent:
            recent = report_service._db.fetchall(
                "SELECT o.id, o.order_number, o.order_type, o.total, o.created_at, "
                "COALESCE(t.table_no,'-') table_no FROM orders o "
                "LEFT JOIN tables t ON t.id=o.table_id WHERE o.status IN ('paid','closed') "
                "ORDER BY o.id DESC LIMIT 12"
            )
        self.recent_table.setRowCount(len(recent))
        for i, r in enumerate(recent):
            type_label = {"dine-in": "Dine-in", "takeaway": "TakeAway", "delivery": "Delivery"}.get(
                r["order_type"], r["order_type"])
            self.recent_table.setItem(i, 0, QTableWidgetItem(f"#{r['order_number']}"))
            self.recent_table.setItem(i, 1, QTableWidgetItem(type_label))
            self.recent_table.setItem(i, 2, QTableWidgetItem(fmt_money(r["total"], currency)))
            self.recent_table.setItem(i, 3, QTableWidgetItem(fmt_datetime(r["created_at"])))
        self.recent_table.resizeColumnsToContents()
