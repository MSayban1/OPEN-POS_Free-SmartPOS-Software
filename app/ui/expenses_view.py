import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDateEdit, QDialog, QDoubleSpinBox, QFormLayout, QFrame, QHBoxLayout,
    QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.services.auth_service import auth_service
from app.services.expense_service import expense_service
from app.services.settings_service import settings_service
from app.ui.keys import bind_table_keys
from app.utils.helpers import fmt_money


class ExpenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Expense")
        self.setFixedWidth(420)
        form = QFormLayout(self)
        form.setSpacing(12)

        self.cat = QComboBox()
        self.cat.addItem("— Uncategorized —", None)
        for c in expense_service.list_categories():
            self.cat.addItem(c["name"], c["id"])
        self.desc = QLineEdit()
        self.desc.setPlaceholderText("What was this for?")
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 100_000_000)
        self.amount.setDecimals(2)
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(datetime.date.today())

        form.addRow("Category", self.cat)
        form.addRow("Description", self.desc)
        form.addRow("Amount", self.amount)
        form.addRow("Date", self.date)

        btns = QHBoxLayout()
        save = QPushButton("Save")
        save.setProperty("primary", True)
        save.clicked.connect(self._save)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btns.addWidget(cancel)
        btns.addWidget(save)
        form.addRow(btns)

    def _save(self):
        if self.amount.value() <= 0:
            QMessageBox.warning(self, "Validation", "Enter a valid amount.")
            return
        self.accept()


class CategoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Expense Categories")
        self.resize(380, 460)
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        form = QHBoxLayout()
        self.new_name = QLineEdit()
        self.new_name.setPlaceholderText("New category name")
        add = QPushButton("+  Add")
        add.setProperty("primary", True)
        add.clicked.connect(self._add)
        form.addWidget(self.new_name, 1)
        form.addWidget(add)
        root.addLayout(form)

        self.list = QListWidget()
        self.list.setFrameShape(QFrame.NoFrame)
        root.addWidget(self.list, 1)

        btn_row = QHBoxLayout()
        delete = QPushButton("Delete Selected")
        delete.setProperty("danger", True)
        delete.clicked.connect(self._delete)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        btn_row.addStretch()
        btn_row.addWidget(delete)
        btn_row.addWidget(close)
        root.addLayout(btn_row)

        if (auth_service.current_user or {}).get("role") == "cashier":
            delete.setVisible(False)

        self._reload()

    def _reload(self):
        self.list.clear()
        for c in expense_service.list_categories():
            it = QListWidgetItem(c["name"])
            it.setData(Qt.UserRole, c["id"])
            self.list.addItem(it)

    def _add(self):
        name = self.new_name.text().strip()
        if not name:
            return
        try:
            expense_service.add_category(name)
        except Exception:
            QMessageBox.warning(self, "Error", "Category may already exist.")
            return
        self.new_name.clear()
        self._reload()

    def _delete(self):
        it = self.list.currentItem()
        if not it:
            return
        name = it.text()
        if QMessageBox.question(self, "Delete Category",
                                f"Delete category '{name}'?") == QMessageBox.Yes:
            expense_service.delete_category(it.data(Qt.UserRole))
            self._reload()


class ExpensesView(QWidget):
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
        title = QLabel("Expenses")
        title.setObjectName("PageTitle")
        sub = QLabel("Track your daily spending by category")
        sub.setObjectName("PageSubtitle")
        t.addWidget(title)
        t.addWidget(sub)
        head.addLayout(t)
        head.addStretch()
        self.summary_lbl = QLabel("")
        self.summary_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #ef4444;")
        head.addWidget(self.summary_lbl)
        outer.addLayout(head)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        add = QPushButton("+  Add Expense")
        add.setProperty("primary", True)
        add.clicked.connect(self._add_expense)
        btns.addWidget(add)
        self.manage_btn = QPushButton("Manage Categories")
        self.manage_btn.clicked.connect(self._manage_categories)
        btns.addWidget(self.manage_btn)
        btns.addStretch()
        outer.addLayout(btns)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Date", "Category", "Description", "Amount"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        outer.addWidget(self.table, 1)

        del_btn = QPushButton("Delete Selected")
        del_btn.setProperty("danger", True)
        del_btn.clicked.connect(self._delete)
        self.del_btn = del_btn
        outer.addWidget(del_btn, alignment=Qt.AlignRight)

        self._apply_role_restrictions()

        bind_table_keys(self.table, on_delete=self._delete)

    def _apply_role_restrictions(self):
        role = (auth_service.current_user or {}).get("role")
        if role == "cashier":
            self.manage_btn.setVisible(False)
            self.del_btn.setVisible(False)

        self.refresh()

    def refresh(self):
        start = datetime.date.today().replace(day=1).isoformat()
        end = datetime.date.today().isoformat()
        expenses = expense_service.list()
        self.table.setRowCount(len(expenses))
        currency = settings_service.get("currency", "Rs")
        for i, e in enumerate(expenses):
            self.table.setItem(i, 0, QTableWidgetItem(e["expense_date"]))
            self.table.setItem(i, 1, QTableWidgetItem(e["category_name"] or "—"))
            self.table.setItem(i, 2, QTableWidgetItem(e["description"] or ""))
            self.table.setItem(i, 3, QTableWidgetItem(fmt_money(e["amount"], currency)))
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(2, 300)
        monthly = expense_service.total_between(start, end)
        self.summary_lbl.setText(f"This Month: {fmt_money(monthly, currency)}")

    def _add_expense(self):
        dlg = ExpenseDialog(self)
        if dlg.exec():
            expense_service.add(dlg.cat.currentData(), dlg.desc.text().strip(),
                                dlg.amount.value(),
                                dlg.date.date().toString("yyyy-MM-dd"))
            self.refresh()

    def _delete(self):
        if (auth_service.current_user or {}).get("role") == "cashier":
            return
        row = self.table.currentRow()
        if row < 0:
            return
        expense = expense_service.list()[row]
        if QMessageBox.question(self, "Delete", "Delete this expense?") == QMessageBox.Yes:
            expense_service.delete(expense["id"])
            self.refresh()

    def _manage_categories(self):
        if (auth_service.current_user or {}).get("role") == "cashier":
            return
        dlg = CategoryDialog(self)
        dlg.exec()
