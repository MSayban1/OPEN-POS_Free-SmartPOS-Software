from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout,
    QWidget,
)

from app.services.table_service import table_service
from app.ui.icons import icon_pixmap, make_icon
from app.ui.table_popup import TablePopup
from app.utils.helpers import fmt_datetime

STATUS_COLORS = {
    "free": "#10b981",
    "occupied": "#ef4444",
    "request_bill": "#f59e0b",
}

STATUS_TEXT = {
    "free": "FREE",
    "occupied": "OCCUPIED",
    "request_bill": "REQUEST BILL",
}


class DiningView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(14)

        head = QHBoxLayout()
        t = QVBoxLayout()
        title = QLabel("Dining")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Tap a table to open the order screen")
        subtitle.setObjectName("PageSubtitle")
        t.addWidget(title)
        t.addWidget(subtitle)
        head.addLayout(t)
        head.addStretch()
        self.refresh_btn = QPushButton("   Refresh")
        self.refresh_btn.setIcon(make_icon("refresh", "#4b5563", 24))
        self.refresh_btn.setIconSize(QSize(18, 18))
        self.refresh_btn.clicked.connect(self.refresh)
        head.addWidget(self.refresh_btn)
        outer.addLayout(head)

        legend = QHBoxLayout()
        for key, label in STATUS_TEXT.items():
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {STATUS_COLORS[key]}; font-size: 14px;")
            lbl = QLabel(label)
            lbl.setProperty("muted", True)
            legend.addWidget(dot)
            legend.addWidget(lbl)
            legend.addSpacing(14)
        legend.addStretch()
        outer.addLayout(legend)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(14)
        self.scroll.setWidget(self.container)
        outer.addWidget(self.scroll, 1)

    def refresh(self):
        while self.grid.count():
            it = self.grid.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()
        tables = table_service.list_all()
        cols = max(4, (self.width() // 210))
        for i, t in enumerate(tables):
            row, col = divmod(i, cols)
            self.grid.addWidget(self._table_card(t), row, col)
        self.grid.setRowStretch((len(tables) - 1) // cols + 1, 1)

    def _table_card(self, table):
        status = table["status"]
        color = STATUS_COLORS.get(status, "#6b7280")
        card = QFrame()
        card.setObjectName("TableCard")
        card.setStyleSheet(
            f"QFrame#TableCard {{ background: {color}; border-radius: 18px; }}"
            f"QFrame#TableCard:hover {{ background: {color}; border: 3px solid #11182733; }}"
        )
        card.setMinimumHeight(130)
        card.setCursor(Qt.PointingHandCursor)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4)

        top = QHBoxLayout()
        no = QLabel(table["table_no"])
        no.setObjectName("TableNo")
        top.addWidget(no)
        top.addStretch()
        seats_ic = QLabel()
        seats_ic.setPixmap(icon_pixmap("user", "#ffffff", 14))
        top.addWidget(seats_ic)
        seats = QLabel(f"{table['seats']} seats")
        seats.setStyleSheet("color: rgba(255,255,255,0.95); font-weight: 600;")
        top.addWidget(seats)
        lay.addLayout(top)

        badge = QLabel(STATUS_TEXT.get(status, status.upper()))
        badge.setStyleSheet(
            "background: rgba(255,255,255,0.22); color: white; font-weight: 800; "
            "font-size: 11px; padding: 3px 10px; border-radius: 10px;"
        )
        lay.addWidget(badge)

        if status != "free" and table["waiter_name"]:
            wrow = QHBoxLayout()
            wic = QLabel()
            wic.setPixmap(icon_pixmap("user", "#ffffff", 14))
            wrow.addWidget(wic)
            w = QLabel(f"  {table['waiter_name']}")
            w.setStyleSheet("color: rgba(255,255,255,0.95); font-size: 12px; font-weight: 600;")
            wrow.addWidget(w)
            wrow.addStretch()
            lay.addLayout(wrow)
        if table["current_total"]:
            tot = QLabel(f"Total: {table['current_total']:,.2f}")
            tot.setStyleSheet("color: rgba(255,255,255,0.95); font-size: 12px; font-weight: 800;")
            lay.addWidget(tot)
        if table["opened_at"]:
            tm = QLabel(fmt_datetime(table["opened_at"]))
            tm.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 10px;")
            lay.addWidget(tm)

        tid = table["id"]
        card.mousePressEvent = lambda _e, _id=tid: self._open_table(_id)
        return card

    def _open_table(self, table_id):
        table = table_service.get(table_id)
        dlg = TablePopup(table)
        dlg.exec()
        self.refresh()
