from PySide6.QtWidgets import (
    QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout, QInputDialog,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.services.product_service import product_service
from app.services.settings_service import settings_service
from app.ui.icons import make_icon
from app.ui.keys import bind_table_keys


class ProductDialog(QDialog):
    def __init__(self, parent=None, product=None, categories=None):
        super().__init__(parent)
        self.product = product
        self.setWindowTitle("Edit Product" if product else "Add Product")
        self.setFixedWidth(400)
        form = QFormLayout(self)
        form.setSpacing(10)

        self.name = QLineEdit()
        self.cat = QComboBox()
        self.cat.addItem("— None —", None)
        for c in categories or []:
            self.cat.addItem(c["name"], c["id"])
        self.price = QDoubleSpinBox()
        self.price.setRange(0, 1_000_000)
        self.price.setDecimals(2)
        self.cost = QDoubleSpinBox()
        self.cost.setRange(0, 1_000_000)
        self.cost.setDecimals(2)

        form.addRow("Name", self.name)
        form.addRow("Category", self.cat)
        form.addRow("Price", self.price)
        form.addRow("Cost", self.cost)

        btns = QHBoxLayout()
        save = QPushButton("Save")
        save.setProperty("primary", True)
        save.clicked.connect(self.accept)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        btns.addWidget(save)
        form.addRow(btns)

        if product:
            self.name.setText(product["name"])
            idx = self.cat.findData(product["category_id"])
            if idx >= 0:
                self.cat.setCurrentIndex(idx)
            self.price.setValue(product["price"])
            self.cost.setValue(product["cost"])

    def values(self):
        return {
            "name": self.name.text().strip(),
            "category_id": self.cat.currentData(),
            "price": self.price.value(),
            "cost": self.cost.value(),
        }


class ProductsView(QWidget):
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
        title = QLabel("Products")
        title.setObjectName("PageTitle")
        sub = QLabel("Manage menu items and categories")
        sub.setObjectName("PageSubtitle")
        t.addWidget(title)
        t.addWidget(sub)
        head.addLayout(t)
        head.addStretch()
        add = QPushButton("+  Add Product")
        add.setProperty("primary", True)
        add.clicked.connect(self._add_product)
        head.addWidget(add)
        outer.addLayout(head)

        body = QHBoxLayout()
        body.setSpacing(14)

        # categories panel
        cat_card = QFrame()
        cat_card.setProperty("card", True)
        cat_card.setFixedWidth(240)
        cv = QVBoxLayout(cat_card)
        cv.setContentsMargins(12, 12, 12, 12)
        cv.setSpacing(8)
        cv.addWidget(QLabel("Categories"))
        self.cat_list = QTableWidget(0, 1)
        self.cat_list.setHorizontalHeaderLabels(["Name"])
        self.cat_list.horizontalHeader().setStretchLastSection(True)
        self.cat_list.verticalHeader().setVisible(False)
        self.cat_list.setShowGrid(False)
        self.cat_list.setEditTriggers(QTableWidget.NoEditTriggers)
        cv.addWidget(self.cat_list, 1)
        cat_btns = QHBoxLayout()
        b_add = QPushButton("Add")
        b_add.clicked.connect(self._add_category)
        b_edit = QPushButton("Rename")
        b_edit.clicked.connect(self._rename_category)
        b_del = QPushButton("Del")
        b_del.clicked.connect(self._delete_category)
        b_del.setProperty("danger", True)
        cat_btns.addWidget(b_add)
        cat_btns.addWidget(b_edit)
        cat_btns.addWidget(b_del)
        cv.addLayout(cat_btns)
        body.addWidget(cat_card)

        # products panel
        prod_card = QFrame()
        prod_card.setProperty("card", True)
        pv = QVBoxLayout(prod_card)
        pv.setContentsMargins(14, 12, 14, 12)
        pv.setSpacing(10)
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("  Search products...")
        self.search.addAction(make_icon("search", "#9ca3af", 24), QLineEdit.LeadingPosition)
        self.search.textChanged.connect(self.refresh)
        search_row.addWidget(self.search)
        self.cat_filter = QComboBox()
        self.cat_filter.addItem("All Categories", None)
        self.cat_filter.currentIndexChanged.connect(lambda _: self.refresh())
        search_row.addWidget(self.cat_filter)
        pv.addLayout(search_row)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Category", "Price", "Cost"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        pv.addWidget(self.table, 1)

        row_btns = QHBoxLayout()
        b_edit = QPushButton("Edit")
        b_edit.clicked.connect(self._edit_product)
        b_del = QPushButton("Delete")
        b_del.setProperty("danger", True)
        b_del.clicked.connect(self._delete_product)
        row_btns.addStretch()
        row_btns.addWidget(b_edit)
        row_btns.addWidget(b_del)
        pv.addLayout(row_btns)
        body.addWidget(prod_card, 1)

        outer.addLayout(body, 1)

        bind_table_keys(self.table, on_enter=self._edit_product, on_delete=self._delete_product)
        bind_table_keys(self.cat_list, on_enter=self._rename_category, on_delete=self._delete_category)

    def refresh(self):
        cats = product_service.list_categories()
        self.cat_filter.blockSignals(True)
        cur = self.cat_filter.currentData()
        self.cat_filter.clear()
        self.cat_filter.addItem("All Categories", None)
        for c in cats:
            self.cat_filter.addItem(c["name"], c["id"])
        idx = self.cat_filter.findData(cur)
        if idx >= 0:
            self.cat_filter.setCurrentIndex(idx)
        self.cat_filter.blockSignals(False)

        self.cat_list.setRowCount(len(cats))
        for i, c in enumerate(cats):
            self.cat_list.setItem(i, 0, QTableWidgetItem(c["name"]))
        self.cat_list.resizeRowsToContents()

        cat_id = self.cat_filter.currentData()
        products = product_service.list_active("", None)
        if cat_id:
            products = [p for p in products if p["category_id"] == cat_id]
        s = self.search.text().strip().lower()
        if s:
            products = [p for p in products if s in p["name"].lower()]

        self.table.setRowCount(len(products))
        for i, p in enumerate(products):
            self.table.setItem(i, 0, QTableWidgetItem(str(p["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(p["name"]))
            self.table.setItem(i, 2, QTableWidgetItem(p["category_name"] or "—"))
            self.table.setItem(i, 3, QTableWidgetItem(f"{p['price']:,.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"{p['cost']:,.2f}"))
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(1, 240)

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def _add_product(self):
        dlg = ProductDialog(self, categories=product_service.list_categories())
        if dlg.exec():
            v = dlg.values()
            if not v["name"]:
                QMessageBox.warning(self, "Validation", "Name is required.")
                return
            product_service.add(v["name"], v["price"], v["cost"], v["category_id"])
            self.refresh()

    def _edit_product(self):
        pid = self._selected_id()
        if not pid:
            return
        p = product_service.get(pid)
        dlg = ProductDialog(self, product=p, categories=product_service.list_categories())
        if dlg.exec():
            v = dlg.values()
            product_service.update(pid, v["name"], v["price"], v["cost"], v["category_id"], True)
            self.refresh()

    def _delete_product(self):
        pid = self._selected_id()
        if not pid:
            return
        if QMessageBox.question(self, "Delete", "Delete this product?") == QMessageBox.Yes:
            product_service.delete(pid)
            self.refresh()

    def _add_category(self):
        name, ok = QInputDialog.getText(self, "Add Category", "Category name:")
        if ok and name.strip():
            product_service.add_category(name.strip())
            self.refresh()

    def _rename_category(self):
        row = self.cat_list.currentRow()
        if row < 0:
            return
        c = product_service.list_categories()[row]
        name, ok = QInputDialog.getText(self, "Rename Category", "Category name:", text=c["name"])
        if ok and name.strip():
            product_service.update_category(c["id"], name.strip())
            self.refresh()

    def _delete_category(self):
        row = self.cat_list.currentRow()
        if row < 0:
            return
        c = product_service.list_categories()[row]
        try:
            product_service.delete_category(c["id"])
            self.refresh()
        except ValueError as e:
            QMessageBox.warning(self, "Cannot Delete", str(e))
