from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFrame, QGridLayout, QHBoxLayout, QInputDialog,
    QLabel, QLineEdit, QPushButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget,
    QWidgetItem,
)

from app.services.order_service import order_service
from app.services.product_service import product_service
from app.services.settings_service import settings_service
from app.ui.icons import make_icon
from app.utils.helpers import fmt_money


class ProductGrid(QScrollArea):
    product_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        self._grid = QGridLayout(container)
        self._grid.setContentsMargins(4, 4, 4, 4)
        self._grid.setSpacing(10)
        self.setWidget(container)
        self._buttons = []

    def set_products(self, products, currency="Rs"):
        for b in self._buttons:
            b.deleteLater()
        self._buttons.clear()
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        cols = 3
        for i, p in enumerate(products):
            row, col = divmod(i, cols)
            btn = self._make_card(p, currency)
            self._grid.addWidget(btn, row, col)
            self._buttons.append(btn)

    def _make_card(self, p, currency):
        btn = QPushButton()
        btn.setObjectName("ProductCard")
        btn.setMinimumHeight(86)
        btn.setCursor(Qt.PointingHandCursor)
        lay = QVBoxLayout(btn)
        lay.setContentsMargins(12, 10, 12, 10)
        name = QLabel(p["name"])
        name.setObjectName("ProductName")
        name.setWordWrap(True)
        price = QLabel(fmt_money(p["price"], currency))
        price.setObjectName("ProductPrice")
        lay.addWidget(name)
        lay.addStretch()
        lay.addWidget(price)
        pid = p["id"]
        btn.clicked.connect(lambda _=False, _id=pid: self.product_clicked.emit(_id))
        return btn


class CartPanel(QFrame):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.order_id = None
        self._build()

    def _build(self):
        self.setProperty("card", True)
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # ---- Left: product browser ----
        left = QVBoxLayout()
        left.setSpacing(10)
        self.search = QLineEdit()
        self.search.setObjectName("SearchBox")
        self.search.setPlaceholderText("  Search products...")
        self.search.addAction(make_icon("search", "#9ca3af", 24), QLineEdit.LeadingPosition)
        self.search.textChanged.connect(self._reload_products)
        left.addWidget(self.search)

        chip_scroll = QScrollArea()
        chip_scroll.setWidgetResizable(True)
        chip_scroll.setFixedHeight(44)
        chip_scroll.setFrameShape(QFrame.NoFrame)
        chip_container = QWidget()
        self.chips = QHBoxLayout(chip_container)
        self.chips.setContentsMargins(0, 0, 0, 0)
        self.chips.setSpacing(8)
        chip_scroll.setWidget(chip_container)
        left.addWidget(chip_scroll)

        self.grid = ProductGrid()
        left.addWidget(self.grid, 1)
        root.addLayout(left, 5)

        # ---- Right: cart ----
        right = QVBoxLayout()
        right.setSpacing(10)
        head = QHBoxLayout()
        title = QLabel("Current Order")
        title.setObjectName("SectionHeader")
        head.addWidget(title)
        head.addStretch()
        self.count_lbl = QLabel("0 items")
        self.count_lbl.setProperty("muted", True)
        head.addWidget(self.count_lbl)
        right.addLayout(head)

        self.items_area = QScrollArea()
        self.items_area.setWidgetResizable(True)
        self.items_area.setFrameShape(QFrame.NoFrame)
        self.items_area.setMinimumWidth(340)
        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 4, 0)
        self.items_layout.setSpacing(8)
        self.items_layout.addStretch()
        self.items_area.setWidget(self.items_container)
        right.addWidget(self.items_area, 1)

        self.note = QLineEdit()
        self.note.setPlaceholderText("  Order / table instructions...")
        self.note.addAction(make_icon("pencil", "#9ca3af", 24), QLineEdit.LeadingPosition)
        self.note.editingFinished.connect(self._save_note)
        right.addWidget(self.note)

        disc_row = QHBoxLayout()
        self.disc_type = QComboBox()
        self.disc_type.addItems(["Amount", "Percent"])
        self.disc_type.setFixedWidth(90)
        self.disc_type.currentIndexChanged.connect(self._disc_type_changed)
        disc_row.addWidget(self.disc_type)
        self.disc_value = QDoubleSpinBox()
        self.disc_value.setRange(0, 1000000)
        self.disc_value.setDecimals(2)
        self.disc_value.valueChanged.connect(self._save_discount)
        disc_row.addWidget(self.disc_value, 1)
        right.addLayout(disc_row)

        totals = QFrame()
        totals.setObjectName("TotalsBox")
        tlay = QVBoxLayout(totals)
        tlay.setContentsMargins(16, 13, 16, 13)
        tlay.setSpacing(7)
        self.t_subtotal = self._total_row(tlay, "Subtotal")
        self.t_discount = self._total_row(tlay, "Discount")
        self.t_tax = self._total_row(tlay, "Tax")
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background: #e5e7eb;")
        tlay.addWidget(line)
        self.t_total = self._total_row(tlay, "TOTAL", bold=True, value_size=15)
        right.addWidget(totals)

        root.addLayout(right, 4)

    def _total_row(self, lay, label, bold=False, value_size=None):
        row = QHBoxLayout()
        row.setSpacing(12)
        lbl = QLabel(label)
        font = lbl.font()
        font.setBold(bold)
        lbl.setFont(font)
        lbl.setMinimumHeight(22)
        val = QLabel("Rs 0.00")
        if value_size:
            vfont = val.font()
            vfont.setPointSizeF(value_size)
            vfont.setBold(True)
            val.setFont(vfont)
        else:
            val.setFont(font)
        val.setAlignment(Qt.AlignRight)
        val.setMinimumHeight(22)
        row.addWidget(lbl)
        row.addWidget(val)
        lay.addLayout(row)
        return val

    def _reload_products(self):
        cat_id = self.chips.property("selected")
        products = product_service.list_active(self.search.text().strip(), cat_id)
        self.grid.set_products(products, settings_service.get("currency", "Rs"))

    def load_categories(self):
        while self.chips.count():
            it = self.chips.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()
        all_btn = QPushButton("All")
        all_btn.setObjectName("ChipButton")
        all_btn.setCheckable(True)
        all_btn.setChecked(True)
        all_btn.clicked.connect(lambda: self._select_category(None, all_btn))
        self.chips.addWidget(all_btn)
        for cat in product_service.list_categories():
            b = QPushButton(cat["name"])
            b.setObjectName("ChipButton")
            b.setCheckable(True)
            b.clicked.connect(lambda _=False, cid=cat["id"], btn=b: self._select_category(cid, btn))
            self.chips.addWidget(b)
        self.chips.addStretch()
        self.chips.setProperty("selected", None)
        self._reload_products()

    def _select_category(self, cat_id, btn):
        for i in range(self.chips.count()):
            it = self.chips.itemAt(i)
            w = it.widget()
            if isinstance(w, QPushButton):
                w.setChecked(w is btn)
        self.chips.setProperty("selected", cat_id)
        self._reload_products()

    # ---- order binding ----
    def load_order(self, order_id):
        self.order_id = order_id
        if order_id is None:
            self.note.blockSignals(True)
            self.note.clear()
            self.note.blockSignals(False)
            self.disc_type.blockSignals(True)
            self.disc_type.setCurrentIndex(0)
            self.disc_type.blockSignals(False)
            self.disc_value.blockSignals(True)
            self.disc_value.setValue(0)
            self.disc_value.blockSignals(False)
            self._reset_totals()
            self.refresh()
            return
        order = order_service.get(order_id)
        self.note.blockSignals(True)
        self.note.setText(order["instructions"] or "")
        self.note.blockSignals(False)
        self.disc_value.blockSignals(True)
        self.disc_value.setValue(float(order["discount"] or 0))
        self.disc_value.blockSignals(False)
        idx = self.disc_type.findText(order["discount_type"].capitalize())
        self.disc_type.setCurrentIndex(max(0, idx))
        self.refresh()

    def _reset_totals(self):
        zero = fmt_money(0, settings_service.get("currency", "Rs"))
        self.t_subtotal.setText(zero)
        self.t_discount.setText(zero)
        self.t_tax.setText(zero)
        self.t_total.setText(zero)
        self.count_lbl.setText("0 items")

    def refresh(self):
        self._reload_items()
        self._reload_totals()

    def _reload_items(self):
        for i in reversed(range(self.items_layout.count())):
            it = self.items_layout.itemAt(i)
            if isinstance(it, QWidgetItem):
                it.widget().deleteLater()
        if self.order_id is None:
            return
        items = order_service.get_items(self.order_id)
        total_qty = sum(float(i["qty"]) for i in items)
        self.count_lbl.setText(f"{int(total_qty)} items")
        for it in items:
            row = self._item_row(it)
            self.items_layout.insertWidget(self.items_layout.count() - 1, row)

    def _item_row(self, item):
        frame = QFrame()
        frame.setObjectName("MenuItemRow")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(12, 8, 8, 8)
        lay.setSpacing(8)
        name_lbl = QLabel(item["name"])
        name_lbl.setWordWrap(True)
        lay.addWidget(name_lbl, 1)

        minus = QPushButton()
        minus.setObjectName("QtyBtn")
        minus.setIcon(make_icon("minus", "#ef4444", 24))
        minus.setIconSize(QSize(14, 14))
        plus = QPushButton()
        plus.setObjectName("QtyBtn")
        plus.setIcon(make_icon("plus", "#10b981", 24))
        plus.setIconSize(QSize(14, 14))
        qty_lbl = QLabel(str(item["qty"]))
        qty_lbl.setAlignment(Qt.AlignCenter)
        qty_lbl.setFixedWidth(32)

        note_btn = QPushButton()
        note_btn.setObjectName("QtyBtn")
        note_btn.setIcon(make_icon("pencil", "#6b7280", 24))
        note_btn.setIconSize(QSize(14, 14))
        note_btn.setToolTip("Item note")
        del_btn = QPushButton()
        del_btn.setObjectName("QtyBtn")
        del_btn.setIcon(make_icon("close", "#ef4444", 24))
        del_btn.setIconSize(QSize(14, 14))

        minus.clicked.connect(lambda _=False, iid=item["id"]: self._change_qty(iid, -1))
        plus.clicked.connect(lambda _=False, iid=item["id"]: self._change_qty(iid, +1))
        note_btn.clicked.connect(lambda _=False, iid=item["id"]: self._edit_item_note(iid))
        del_btn.clicked.connect(lambda _=False, iid=item["id"]: self._remove_item(iid))

        lay.addWidget(minus)
        lay.addWidget(qty_lbl)
        lay.addWidget(plus)
        lay.addWidget(note_btn)
        lay.addWidget(del_btn)
        return frame

    def _change_qty(self, item_id, delta):
        items = order_service.get_items(self.order_id)
        current = next((i for i in items if i["id"] == item_id), None)
        if not current:
            return
        order_service.update_qty(item_id, int(current["qty"]) + delta)
        self.refresh()
        self.changed.emit()

    def _edit_item_note(self, item_id):
        items = order_service.get_items(self.order_id)
        current = next((i for i in items if i["id"] == item_id), None)
        if not current:
            return
        text, ok = QInputDialog.getText(self, "Item Note", "Instructions for this item:",
                                        text=current["instructions"] or "")
        if ok:
            order_service.set_item_instructions(item_id, text)
            self.refresh()

    def _remove_item(self, item_id):
        order_service.remove_item(item_id)
        self.refresh()
        self.changed.emit()

    def _save_note(self):
        if self.order_id:
            order_service.set_order_instructions(self.order_id, self.note.text().strip())

    def _disc_type_changed(self):
        if self.order_id:
            order_service.set_discount(self.order_id, self.disc_value.value(),
                                       self.disc_type.currentText().lower())
            self._reload_totals()

    def _save_discount(self, value):
        if self.order_id:
            order_service.set_discount(self.order_id, value, self.disc_type.currentText().lower())
            self._reload_totals()

    def _reload_totals(self):
        if not self.order_id:
            return
        order = order_service.get(self.order_id)
        currency = settings_service.get("currency", "Rs")
        self.t_subtotal.setText(fmt_money(order["subtotal"], currency))
        self.t_discount.setText(f"- {fmt_money(order['discount'], currency)}" if order["discount"] else "Rs 0.00")
        self.t_tax.setText(fmt_money(order["tax"], currency))
        self.t_total.setText(fmt_money(order["total"], currency))
