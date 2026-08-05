from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QVBoxLayout, QWidget,
)

from app.printing.printer_service import (
    print_final_bill, print_kot, print_request_bill,
)
from app.services.auth_service import auth_service
from app.services.order_service import order_service
from app.services.staff_service import staff_service
from app.services.table_service import table_service
from app.ui.cart_panel import CartPanel
from app.ui.icons import make_icon

STATUS_LABEL = {"free": "FREE", "occupied": "OCCUPIED", "request_bill": "REQUEST BILL"}


class TablePopup(QDialog):
    def __init__(self, table, parent=None):
        super().__init__(parent)
        self.table = dict(table) if hasattr(table, "keys") else table
        self.order = None
        self.setWindowTitle(f"Table {table['table_no']}")
        self.resize(1080, 640)
        self.setModal(True)
        self._build()
        self._init_order()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        head = QHBoxLayout()
        title = QLabel(f"Table {self.table['table_no']}  ·  {self.table['seats']} seats")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #111827;")
        head.addWidget(title)
        status = QLabel()
        status.setStyleSheet("font-weight: 800; font-size: 12px; padding: 5px 14px; border-radius: 12px;")
        st = self.table["status"]
        status.setText(STATUS_LABEL.get(st, st.upper()))
        bg = {"free": "#10b981", "occupied": "#ef4444", "request_bill": "#f59e0b"}.get(st, "#6b7280")
        status.setStyleSheet(f"background: {bg}22; color: {bg}; font-weight: 800; padding: 4px 12px; border-radius: 12px;")
        head.addWidget(status)
        head.addStretch()
        head.addWidget(QLabel("Waiter:"))

        self.waiter = QComboBox()
        self.waiter.setMinimumWidth(180)
        self.waiters = staff_service.list_waiters()
        self.waiter.addItem("— Select Waiter —", None)
        for w in self.waiters:
            self.waiter.addItem(w["name"], w["id"])
        self.waiter.currentIndexChanged.connect(self._waiter_changed)
        head.addWidget(self.waiter)
        root.addLayout(head)

        self.cart = CartPanel()
        self.cart.grid.product_clicked.connect(self._add_product)
        self.cart.load_categories()
        root.addWidget(self.cart, 1)

        actions = QHBoxLayout()
        actions.setSpacing(10)

        self.btn_kot = QPushButton("   Print KOT")
        self.btn_kot.setProperty("warning", True)
        self.btn_kot.setIcon(make_icon("print", "#ffffff", 24))
        self.btn_kot.setIconSize(QSize(18, 18))
        self.btn_kot.clicked.connect(self._do_kot)

        self.btn_request = QPushButton("   Request Bill")
        self.btn_request.setProperty("primary", True)
        self.btn_request.setIcon(make_icon("note", "#ffffff", 24))
        self.btn_request.setIconSize(QSize(18, 18))
        self.btn_request.clicked.connect(self._do_request_bill)

        self.pay_label = QLabel("Payment:")
        self.payment = QComboBox()
        self.payment.addItems(["Cash", "Card", "QR"])

        self.btn_final = QPushButton("   Final Bill & Close")
        self.btn_final.setProperty("success", True)
        self.btn_final.setIcon(make_icon("check", "#ffffff", 24))
        self.btn_final.setIconSize(QSize(18, 18))
        self.btn_final.clicked.connect(self._do_final_bill)

        self.btn_close = QPushButton("Close Table")
        self.btn_close.clicked.connect(self._do_manual_close)

        actions.addWidget(self.btn_kot)
        actions.addWidget(self.btn_request)
        actions.addStretch()
        actions.addWidget(self.pay_label)
        actions.addWidget(self.payment)
        actions.addWidget(self.btn_final)
        actions.addWidget(self.btn_close)
        root.addLayout(actions)

    def _init_order(self):
        if self.table["status"] != "free":
            order = order_service.get_open_order_for_table(self.table["id"])
            if order:
                self.order = order
                idx = self.waiter.findData(order["waiter_id"])
                if idx >= 0:
                    self.waiter.setCurrentIndex(idx)
                self.cart.load_order(order["id"])
                self.btn_final.setEnabled(True)
                self.btn_request.setEnabled(True)
                self.btn_kot.setEnabled(True)
                return
        # free table -> create order when first product added
        self.order = None
        self.btn_final.setEnabled(False)
        self.btn_request.setEnabled(False)
        self.btn_kot.setEnabled(False)

    def _ensure_order(self):
        if self.order is None:
            self.order = order_service.create_order(
                table_id=self.table["id"],
                waiter_id=self.waiter.currentData(),
                cashier_id=auth_service.current_user["id"],
                order_type="dine-in",
                instructions=self.cart.note.text().strip(),
            )
            table_service.set_status(self.table["id"], "occupied", self.order["id"])
            self.table["status"] = "occupied"
            self.cart.load_order(self.order["id"])
            self.btn_final.setEnabled(True)
            self.btn_request.setEnabled(True)
            self.btn_kot.setEnabled(True)
        return self.order

    def _add_product(self, product_id):
        order = self._ensure_order()
        order_service.add_item(order["id"], product_id=product_id, qty=1)
        self.cart.refresh()

    def _waiter_changed(self, idx):
        if self.order is not None:
            order_service.set_waiter(self.order["id"], self.waiter.currentData())

    def _do_kot(self):
        order = self._ensure_order()
        if not order_service.get_items(order["id"]):
            QMessageBox.information(self, "Empty Order", "Add items before printing KOT.")
            return
        try:
            print_kot(order)
        except Exception as e:
            QMessageBox.critical(self, "Print Error", str(e))

    def _do_request_bill(self):
        order = self._ensure_order()
        if not order_service.get_items(order["id"]):
            QMessageBox.information(self, "Empty Order", "Add items before requesting bill.")
            return
        order_service.request_bill(order["id"])
        self.table["status"] = "request_bill"
        try:
            print_request_bill(order_service.get(order["id"]))
        except Exception as e:
            QMessageBox.critical(self, "Print Error", str(e))
        self.accept()

    def _do_final_bill(self):
        order = self._ensure_order()
        if not order_service.get_items(order["id"]):
            QMessageBox.information(self, "Empty Order", "Add items before final bill.")
            return
        method = self.payment.currentText()
        resp = QMessageBox.question(
            self, "Confirm Payment",
            f"Close this bill and print Final Bill?\n\nTotal: {self.cart.t_total.text()}\nPayment: {method}",
        )
        if resp != QMessageBox.Yes:
            return
        order_service.finalize(order["id"], method)
        self.table["status"] = "free"
        try:
            print_final_bill(order_service.get(order["id"]))
        except Exception as e:
            QMessageBox.critical(self, "Print Error", str(e))
        self.accept()

    def _do_manual_close(self):
        if self.order is not None and order_service.get_items(self.order["id"]):
            resp = QMessageBox.question(
                self, "Close Table",
                "Table has items but no payment will be recorded. Close anyway?",
            )
            if resp != QMessageBox.Yes:
                return
            order_service.manual_close(self.order["id"])
        else:
            self.order = None
            table_service.set_status(self.table["id"], "free", None)
        self.accept()
