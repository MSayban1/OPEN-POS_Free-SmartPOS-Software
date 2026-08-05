from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QScrollArea, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.printing.printer_service import (
    print_kot, print_request_bill, print_rider_bill,
)
from app.services.auth_service import auth_service
from app.services.order_service import order_service
from app.services.settings_service import settings_service
from app.services.staff_service import staff_service
from app.ui.cart_panel import CartPanel
from app.ui.icons import icon_pixmap, make_icon
from app.ui.keys import bind_table_keys
from app.utils.helpers import fmt_datetime, fmt_money

ORDER_TYPE_LABEL = {"takeaway": "TakeAway", "delivery": "Delivery"}


def _as_dict(row):
    return dict(row) if hasattr(row, "keys") else row


class OrderDetailDialog(QDialog):
    def __init__(self, order, parent=None):
        super().__init__(parent)
        self.order = order
        self.setWindowTitle(f"Order #{order['order_number']}")
        self.resize(460, 560)
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(8)

        currency = settings_service.get("currency", "Rs")

        head = QHBoxLayout()
        t = QLabel(f"Order #{order['order_number']}")
        t.setStyleSheet("font-size: 20px; font-weight: 800;")
        head.addWidget(t)
        head.addStretch()
        st = QLabel(ORDER_TYPE_LABEL.get(order["order_type"], order["order_type"]).upper())
        st.setStyleSheet("background: #eef2ff; color: #4f46e5; font-weight: 800; padding: 4px 12px; border-radius: 12px;")
        head.addWidget(st)
        root.addLayout(head)

        info = []
        info.append(f"Date:   {fmt_datetime(order['created_at'])}")
        if order.get("waiter_name"):
            info.append(f"Waiter:   {order['waiter_name']}")
        if order.get("rider_name"):
            info.append(f"Rider:   {order['rider_name']}")
        if order.get("customer_name"):
            info.append(f"Customer:   {order['customer_name']}")
        if order.get("customer_phone"):
            info.append(f"Phone:   {order['customer_phone']}")
        if order.get("customer_address"):
            info.append(f"Address:   {order['customer_address']}")
        il = QLabel("\n".join(info))
        il.setProperty("muted", True)
        root.addWidget(il)

        self.items = QTableWidget(0, 3)
        self.items.setHorizontalHeaderLabels(["Item", "Qty", "Amount"])
        self.items.verticalHeader().setVisible(False)
        self.items.setEditTriggers(QTableWidget.NoEditTriggers)
        self.items.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.items, 1)
        self._fill_items()

        rows = []
        rows.append(f"Subtotal:   {fmt_money(order['subtotal'], currency)}")
        if order["discount"]:
            rows.append(f"Discount:   - {fmt_money(order['discount'], currency)}")
        if order["tax"]:
            rows.append(f"{settings_service.get('tax_name','Tax')}:   {fmt_money(order['tax'], currency)}")
        if order["service_charge"]:
            label = "Delivery Charge" if order["order_type"] == "delivery" else "Takeaway Charge"
            rows.append(f"{label}:   {fmt_money(order['service_charge'], currency)}")
        rows.append(f"TOTAL:   {fmt_money(order['total'], currency)}")
        tl = QLabel("\n".join(rows))
        tl.setStyleSheet("font-weight: 700; font-size: 14px;")
        root.addWidget(tl)

        btns = QHBoxLayout()
        b_print = QPushButton("   Print Bill")
        b_print.setProperty("primary", True)
        b_print.setIcon(make_icon("print", "#ffffff", 24))
        b_print.setIconSize(QSize(18, 18))
        b_print.clicked.connect(lambda: self._print(print_request_bill))
        btns.addWidget(b_print)
        if order["order_type"] == "delivery" and order.get("rider_name"):
            b_rider = QPushButton("   Print Rider Copy")
            b_rider.setIcon(make_icon("box", "#4b5563", 24))
            b_rider.setIconSize(QSize(18, 18))
            b_rider.clicked.connect(lambda: self._print(print_rider_bill))
            btns.addWidget(b_rider)
        btns.addStretch()
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        btns.addWidget(close)
        root.addLayout(btns)

    def _fill_items(self):
        items = order_service.get_items(self.order["id"])
        currency = settings_service.get("currency", "Rs")
        self.items.setRowCount(len(items))
        for i, it in enumerate(items):
            self.items.setItem(i, 0, QTableWidgetItem(it["name"]))
            self.items.setItem(i, 1, QTableWidgetItem(str(it["qty"])))
            self.items.setItem(i, 2, QTableWidgetItem(fmt_money(it["price"] * it["qty"], currency)))
        self.items.resizeColumnsToContents()

    def _print(self, fn):
        try:
            fn(self.order)
        except Exception as e:
            QMessageBox.critical(self, "Print Error", str(e))


class QuickSalePage(QWidget):
    def __init__(self, order_type, parent=None):
        super().__init__(parent)
        self.order_type = order_type
        self.order_id = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 14, 20, 14)
        root.setSpacing(10)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_new(), "New Order")
        self.tabs.addTab(self._build_pending(), "Pending")
        self.tabs.addTab(self._build_completed(), "Completed")
        self.tabs.currentChanged.connect(lambda _: self._refresh_tab())
        root.addWidget(self.tabs)

    # ---------------- New Order ----------------
    def _build_new(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 8)
        lay.setSpacing(10)

        head = QFrame()
        head.setProperty("card", True)
        vh = QVBoxLayout(head)
        vh.setContentsMargins(16, 10, 16, 10)
        vh.setSpacing(8)

        row1 = QHBoxLayout()
        row1.setSpacing(10)
        row1.addWidget(QLabel("Waiter:"))
        self.waiter = QComboBox()
        self.waiter.setMinimumWidth(150)
        self.waiter.addItem("— Select —", None)
        for s in staff_service.list_waiters():
            self.waiter.addItem(s["name"], s["id"])
        row1.addWidget(self.waiter)

        if self.order_type == "delivery":
            row1.addWidget(QLabel("Rider:"))
            self.rider = QComboBox()
            self.rider.setMinimumWidth(140)
            self.rider.addItem("— Select —", None)
            for s in staff_service.list_riders():
                self.rider.addItem(s["name"], s["id"])
            row1.addWidget(self.rider)
        row1.addStretch()
        charge = settings_service.get_float(
            "delivery_charge" if self.order_type == "delivery" else "takeaway_charge", 0
        )
        self.charge_lbl = QLabel(
            f"Charge: {fmt_money(charge, settings_service.get('currency','Rs'))}"
        )
        self.charge_lbl.setStyleSheet("font-weight: 700; color: #4f46e5;")
        row1.addWidget(self.charge_lbl)
        vh.addLayout(row1)

        if self.order_type == "delivery":
            row2 = QHBoxLayout()
            row2.setSpacing(10)
            self.customer = QLineEdit()
            self.customer.setPlaceholderText("Customer name")
            self.customer.setMinimumWidth(150)
            self.phone = QLineEdit()
            self.phone.setPlaceholderText("Phone")
            self.phone.setMinimumWidth(120)
            self.address = QLineEdit()
            self.address.setPlaceholderText("Delivery address")
            self.address.setMinimumWidth(220)
            row2.addWidget(self.customer)
            row2.addWidget(self.phone)
            row2.addWidget(self.address)
            row2.addStretch()
            vh.addLayout(row2)
        lay.addWidget(head)

        self.cart = CartPanel()
        self.cart.grid.product_clicked.connect(self._add_product)
        self.cart.load_categories()
        lay.addWidget(self.cart, 1)

        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.btn_kot = QPushButton("   Print KOT & Send to Pending")
        self.btn_kot.setProperty("warning", True)
        self.btn_kot.setIcon(make_icon("print", "#ffffff", 24))
        self.btn_kot.setIconSize(QSize(18, 18))
        self.btn_kot.clicked.connect(self._send_to_pending)
        self.btn_clear = QPushButton("   Clear Order")
        self.btn_clear.setIcon(make_icon("trash", "#ef4444", 24))
        self.btn_clear.setIconSize(QSize(18, 18))
        self.btn_clear.clicked.connect(self._clear)
        actions.addWidget(self.btn_kot)
        actions.addStretch()
        actions.addWidget(self.btn_clear)
        lay.addLayout(actions)
        return w

    def _ensure_order(self):
        if self.order_id is not None:
            return self.order_id
        waiter_id = self.waiter.currentData()
        if waiter_id is None:
            QMessageBox.warning(self, "Waiter Required", "Select a waiter first.")
            return None
        rider_id = None
        customer_name = customer_phone = customer_address = ""
        if self.order_type == "delivery":
            rider_id = self.rider.currentData()
            if rider_id is None:
                QMessageBox.warning(self, "Rider Required", "Select a rider first.")
                return None
            customer_name = self.customer.text().strip()
            customer_phone = self.phone.text().strip()
            customer_address = self.address.text().strip()
            if not customer_address:
                QMessageBox.warning(self, "Address Required", "Enter delivery address.")
                return None
        charge = settings_service.get_float(
            "delivery_charge" if self.order_type == "delivery" else "takeaway_charge", 0
        )
        order = order_service.create_order(
            order_type=self.order_type,
            cashier_id=auth_service.current_user["id"],
            waiter_id=waiter_id,
            rider_id=rider_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_address=customer_address,
            service_charge=charge,
        )
        self.order_id = order["id"]
        self.cart.load_order(order["id"])
        return self.order_id

    def _add_product(self, product_id):
        oid = self._ensure_order()
        if oid is None:
            return
        order_service.add_item(oid, product_id=product_id, qty=1)
        self.cart.refresh()

    def _send_to_pending(self):
        oid = self._ensure_order()
        if oid is None:
            return
        if not order_service.get_items(oid):
            QMessageBox.information(self, "Empty Order", "Add items first.")
            return
        order = order_service.get(oid)
        try:
            print_kot(order)
        except Exception as e:
            QMessageBox.critical(self, "Print Error", str(e))
        # Start a fresh order for the next sale so multiple pending orders can coexist.
        self.order_id = None
        self.cart.load_order(None)
        self.tabs.setCurrentIndex(1)
        self._refresh_tab()

    def _clear(self):
        if self.order_id is not None:
            if order_service.get_items(self.order_id):
                resp = QMessageBox.question(
                    self, "Discard Order", "This order has items. Discard it?")
                if resp != QMessageBox.Yes:
                    return
                order_service.manual_close(self.order_id)
            self.order_id = None
        self.cart.load_order(None)
        self.cart.load_categories()

    # ---------------- Pending ----------------
    def _build_pending(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 10, 0, 8)
        self.pending_scroll = QScrollArea()
        self.pending_scroll.setWidgetResizable(True)
        self.pending_scroll.setFrameShape(QFrame.NoFrame)
        self.pending_container = QWidget()
        self.pending_layout = QVBoxLayout(self.pending_container)
        self.pending_layout.setContentsMargins(0, 0, 6, 0)
        self.pending_layout.setSpacing(10)
        self.pending_layout.addStretch()
        self.pending_scroll.setWidget(self.pending_container)
        lay.addWidget(self.pending_scroll)
        return w

    def _refresh_pending(self):
        for i in reversed(range(self.pending_layout.count())):
            it = self.pending_layout.itemAt(i)
            w = it.widget()
            if w:
                w.deleteLater()
        orders = order_service.list_by_type_and_status(self.order_type, ["open"])
        orders = [_as_dict(o) for o in orders if order_service.get_items(o["id"])]
        currency = settings_service.get("currency", "Rs")
        if not orders:
            empty = QLabel("No pending orders.")
            empty.setProperty("muted", True)
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("font-size: 16px; padding: 40px;")
            self.pending_layout.insertWidget(0, empty)
            return
        for o in orders:
            self.pending_layout.insertWidget(
                self.pending_layout.count() - 1, self._pending_card(o, currency)
            )

    def _pending_card(self, order, currency):
        card = QFrame()
        card.setProperty("card", True)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(6)

        head = QHBoxLayout()
        no = QLabel(f"Order #{order['order_number']}")
        no.setStyleSheet("font-size: 16px; font-weight: 800;")
        head.addWidget(no)
        head.addSpacing(12)
        time = QLabel(fmt_datetime(order["created_at"]))
        time.setProperty("muted", True)
        head.addWidget(time)
        head.addStretch()
        total = QLabel(fmt_money(order["total"], currency))
        total.setStyleSheet("font-size: 17px; font-weight: 800; color: #4f46e5;")
        head.addWidget(total)
        lay.addLayout(head)

        line = QLabel(self._order_summary(order))
        line.setWordWrap(True)
        lay.addWidget(line)

        meta = QLabel(self._meta_line(order))
        meta.setProperty("muted", True)
        meta.setWordWrap(True)
        lay.addWidget(meta)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        b_complete = QPushButton("   Mark Completed")
        b_complete.setProperty("success", True)
        b_complete.setIcon(make_icon("tick", "#ffffff", 24))
        b_complete.setIconSize(QSize(18, 18))
        b_complete.setCursor(Qt.PointingHandCursor)
        b_complete.clicked.connect(lambda _=False, oid=order["id"]: self._complete(oid))
        btns.addWidget(b_complete)
        btns.addStretch()
        b_edit = QPushButton("   Edit")
        b_edit.setIcon(make_icon("pencil", "#4b5563", 24))
        b_edit.setIconSize(QSize(18, 18))
        b_edit.setCursor(Qt.PointingHandCursor)
        b_edit.clicked.connect(lambda _=False, oid=order["id"]: self._edit_pending(oid))
        b_cancel = QPushButton("   Cancel")
        b_cancel.setProperty("danger", True)
        b_cancel.setIcon(make_icon("close", "#ffffff", 24))
        b_cancel.setIconSize(QSize(18, 18))
        b_cancel.setCursor(Qt.PointingHandCursor)
        b_cancel.clicked.connect(lambda _=False, oid=order["id"]: self._cancel_pending(oid))
        btns.addWidget(b_edit)
        btns.addWidget(b_cancel)
        lay.addLayout(btns)
        return card

    def _order_summary(self, order):
        items = order_service.get_items(order["id"])
        return "  ·  ".join(f"{it['name']} x{it['qty']:g}" for it in items) or "—"

    def _meta_line(self, order):
        parts = []
        if order.get("waiter_name"):
            parts.append(f"Waiter: {order['waiter_name']}")
        if order.get("rider_name"):
            parts.append(f"Rider: {order['rider_name']}")
        if order.get("customer_name"):
            parts.append(f"Customer: {order['customer_name']}")
        if order.get("customer_phone"):
            parts.append(f"Phone: {order['customer_phone']}")
        if order.get("customer_address"):
            parts.append(f"Address: {order['customer_address']}")
        return "   |   ".join(parts)

    def _complete(self, order_id):
        order = _as_dict(order_service.get(order_id))
        try:
            if self.order_type == "delivery":
                print_rider_bill(order)
                print_request_bill(order)
            else:
                print_request_bill(order)
        except Exception as e:
            QMessageBox.critical(self, "Print Error", str(e))
        order_service.finalize(order_id, "Cash")
        if self.order_id == order_id:
            self.order_id = None
            self.cart.load_order(None)
        self._refresh_tab()

    def _edit_pending(self, order_id):
        order = _as_dict(order_service.get(order_id))
        self.order_id = order_id
        self._load_head(order)
        self.cart.load_order(order_id)
        self.tabs.setCurrentIndex(0)

    def _cancel_pending(self, order_id):
        order = _as_dict(order_service.get(order_id))
        resp = QMessageBox.question(
            self, "Cancel Order",
            f"Cancel order #{order['order_number']}? This cannot be undone.")
        if resp != QMessageBox.Yes:
            return
        order_service.manual_close(order_id)
        if self.order_id == order_id:
            self.order_id = None
            self.cart.load_order(None)
        self._refresh_pending()

    def _load_head(self, order):
        idx = self.waiter.findData(order["waiter_id"])
        self.waiter.setCurrentIndex(max(0, idx))
        if self.order_type == "delivery":
            idx = self.rider.findData(order["rider_id"])
            self.rider.setCurrentIndex(max(0, idx))
            self.customer.setText(order["customer_name"] or "")
            self.phone.setText(order["customer_phone"] or "")
            self.address.setText(order["customer_address"] or "")

    # ---------------- Completed ----------------
    def _build_completed(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 10, 0, 8)
        self.completed_list = QListWidget()
        self.completed_list.setFrameShape(QFrame.NoFrame)
        self.completed_list.itemClicked.connect(self._open_completed)
        lay.addWidget(self.completed_list)
        bind_table_keys(self.completed_list, on_enter=self._open_selected_completed)
        return w

    def _refresh_completed(self):
        self.completed_list.clear()
        orders = [_as_dict(o) for o in order_service.list_by_type_and_status(self.order_type, ["paid"])]
        currency = settings_service.get("currency", "Rs")
        for o in orders:
            name = o.get("customer_name") or o.get("waiter_name") or ""
            txt = f"#{o['order_number']}   {fmt_datetime(o['created_at'])}   {name}   {fmt_money(o['total'], currency)}"
            item = QListWidgetItem(txt)
            item.setData(Qt.UserRole, o["id"])
            item.setIcon(icon_pixmap("note", "#6b7280", 16))
            self.completed_list.addItem(item)

    def _open_completed(self, item):
        oid = item.data(Qt.UserRole)
        order = _as_dict(order_service.get(oid))
        if order:
            dlg = OrderDetailDialog(order, self)
            dlg.exec()

    def _open_selected_completed(self):
        item = self.completed_list.currentItem()
        if item:
            self._open_completed(item)

    # ---------------- misc ----------------
    def _refresh_tab(self):
        idx = self.tabs.currentIndex()
        if idx == 0:
            pass
        elif idx == 1:
            self._refresh_pending()
        elif idx == 2:
            self._refresh_completed()

    def refresh(self):
        self._refresh_tab()


class PosView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(12)
        title = QLabel("Quick Sale")
        title.setObjectName("PageTitle")
        outer.addWidget(title)
        sub = QLabel("TakeAway and Delivery orders")
        sub.setObjectName("PageSubtitle")
        outer.addWidget(sub)

        self.tabs = QTabWidget()
        self.page_takeaway = QuickSalePage("takeaway")
        self.page_delivery = QuickSalePage("delivery")
        self.tabs.addTab(self.page_takeaway, "TakeAway")
        self.tabs.addTab(self.page_delivery, "Delivery")
        outer.addWidget(self.tabs, 1)

    def refresh(self):
        self.page_takeaway._refresh_tab()
        self.page_delivery._refresh_tab()
