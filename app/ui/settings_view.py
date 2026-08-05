import shutil
import uuid

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QFrame, QHBoxLayout,
    QInputDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea, QSpinBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.config import LOGOS_DIR
from app.database.db import get_db
from app.printing.printer_service import list_printers, test_print
from app.services.auth_service import auth_service
from app.services.settings_service import settings_service
from app.services.staff_service import staff_service
from app.services.table_service import table_service
from app.ui.icons import make_icon
from app.ui.keys import bind_table_keys

ROLES = ["cashier", "manager", "admin"]


class SettingsView(QWidget):
    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(14)
        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        outer.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_store_tab(), "Store")
        self.tabs.addTab(self._build_tax_tab(), "Tax Management")
        self.tabs.addTab(self._build_tables_tab(), "Tables")
        self.tabs.addTab(self._build_staff_tab(), "Staff")
        self.tabs.addTab(self._build_users_tab(), "Users")
        self.tabs.addTab(self._build_printing_tab(), "Printing")
        self.tabs.addTab(self._build_backup_tab(), "Backup / Restore")
        outer.addWidget(self.tabs, 1)

    # ---------------- Store ----------------
    def _build_store_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(14)

        card = QFrame()
        card.setProperty("card", True)
        form = QFormLayout(card)
        form.setContentsMargins(20, 18, 20, 18)
        form.setSpacing(12)
        self.s_name = QLineEdit()
        self.s_email = QLineEdit()
        self.s_phone = QLineEdit()
        self.s_address = QLineEdit()
        self.s_currency = QComboBox()
        self.s_currency.addItems(["Rs", "$", "€", "£", "AED", "SAR"])
        form.addRow("Store Name", self.s_name)
        form.addRow("Email", self.s_email)
        form.addRow("Phone", self.s_phone)
        form.addRow("Address", self.s_address)
        form.addRow("Currency", self.s_currency)
        lay.addWidget(card)

        logo_card = QFrame()
        logo_card.setProperty("card", True)
        lv = QVBoxLayout(logo_card)
        lv.setContentsMargins(20, 18, 20, 18)
        lv.setSpacing(8)
        lv.addWidget(QLabel("Store Logo"))
        self.logo_lbl = QLabel("No logo uploaded")
        self.logo_lbl.setProperty("muted", True)
        lv.addWidget(self.logo_lbl)
        btn_row = QHBoxLayout()
        upload = QPushButton("Upload Logo")
        upload.clicked.connect(self._upload_logo)
        remove = QPushButton("Remove")
        remove.clicked.connect(self._remove_logo)
        btn_row.addWidget(upload)
        btn_row.addWidget(remove)
        btn_row.addStretch()
        lv.addLayout(btn_row)
        lay.addWidget(logo_card)

        save = QPushButton("Save Store Settings")
        save.setProperty("primary", True)
        save.clicked.connect(self._save_store)
        lay.addWidget(save, alignment=Qt.AlignRight)
        lay.addStretch()
        return w

    def _upload_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "",
                                              "Images (*.png *.jpg *.jpeg *.bmp)")
        if not path:
            return
        ext = path.rsplit(".", 1)[-1]
        fname = f"logo_{uuid.uuid4().hex[:8]}.{ext}"
        shutil.copy(path, LOGOS_DIR / fname)
        settings_service.set("store_logo", fname)
        self.logo_lbl.setText(f"✓ {fname}")
        QMessageBox.information(self, "Saved", "Logo uploaded. Restart app to apply everywhere.")

    def _remove_logo(self):
        settings_service.set("store_logo", "")
        self.logo_lbl.setText("No logo uploaded")

    def _save_store(self):
        settings_service.set_many({
            "store_name": self.s_name.text().strip(),
            "store_email": self.s_email.text().strip(),
            "store_phone": self.s_phone.text().strip(),
            "store_address": self.s_address.text().strip(),
            "currency": self.s_currency.currentText(),
        })
        QMessageBox.information(self, "Saved", "Store settings saved.")

    # ---------------- Tax Management ----------------
    def _build_tax_tab(self):
        w = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(4, 4, 8, 8)
        lay.setSpacing(14)

        tax = QFrame()
        tax.setProperty("card", True)
        tf = QFormLayout(tax)
        tf.setContentsMargins(20, 18, 20, 18)
        tf.setSpacing(12)
        self.tax_name = QLineEdit()
        self.tax_rate = QDoubleSpinBox()
        self.tax_rate.setRange(0, 100)
        self.tax_rate.setDecimals(2)
        self.tax_rate.setSuffix("  %")
        self.delivery_charge = QDoubleSpinBox()
        self.delivery_charge.setRange(0, 100000)
        self.delivery_charge.setDecimals(2)
        self.takeaway_charge = QDoubleSpinBox()
        self.takeaway_charge.setRange(0, 100000)
        self.takeaway_charge.setDecimals(2)
        tf.addRow("Tax Name", self.tax_name)
        tf.addRow("Tax Rate", self.tax_rate)
        tf.addRow("Delivery Charge (per order)", self.delivery_charge)
        tf.addRow("TakeAway Charge (per order)", self.takeaway_charge)
        lay.addWidget(tax)

        applies = QFrame()
        applies.setProperty("card", True)
        av = QVBoxLayout(applies)
        av.setContentsMargins(20, 18, 20, 18)
        av.setSpacing(8)
        av.addWidget(QLabel("Apply Tax To (order types)"))
        hint = QLabel("Tick the order types that should be charged tax.")
        hint.setProperty("muted", True)
        hint.setWordWrap(True)
        av.addWidget(hint)
        self.tax_dinein = QCheckBox("Dining (Dine-in)")
        self.tax_takeaway = QCheckBox("TakeAway")
        self.tax_delivery = QCheckBox("Delivery")
        av.addWidget(self.tax_dinein)
        av.addWidget(self.tax_takeaway)
        av.addWidget(self.tax_delivery)
        lay.addWidget(applies)

        rec = QFrame()
        rec.setProperty("card", True)
        rf = QVBoxLayout(rec)
        rf.setContentsMargins(20, 18, 20, 18)
        rf.setSpacing(10)
        rf.addWidget(QLabel("Receipt Customization"))
        self.rec_footer = QLineEdit()
        self.rec_footer.setPlaceholderText("Receipt footer message...")
        rf.addWidget(self.rec_footer)
        self.rec_show_logo = QCheckBox("Show logo on receipt")
        self.rec_show_address = QCheckBox("Show address on receipt")
        rf.addWidget(self.rec_show_logo)
        rf.addWidget(self.rec_show_address)
        lay.addWidget(rec)

        save = QPushButton("Save Tax & Receipt Settings")
        save.setProperty("primary", True)
        save.clicked.connect(self._save_receipt)
        lay.addWidget(save, alignment=Qt.AlignRight)
        lay.addStretch()
        scroll.setWidget(inner)
        wlay = QVBoxLayout(w)
        wlay.setContentsMargins(0, 0, 0, 0)
        wlay.addWidget(scroll)
        return w

    def _save_receipt(self):
        settings_service.set_many({
            "tax_name": self.tax_name.text().strip(),
            "tax_rate": str(self.tax_rate.value()),
            "delivery_charge": str(self.delivery_charge.value()),
            "takeaway_charge": str(self.takeaway_charge.value()),
            "tax_dinein": "1" if self.tax_dinein.isChecked() else "0",
            "tax_takeaway": "1" if self.tax_takeaway.isChecked() else "0",
            "tax_delivery": "1" if self.tax_delivery.isChecked() else "0",
            "receipt_footer": self.rec_footer.text().strip(),
            "receipt_show_logo": "1" if self.rec_show_logo.isChecked() else "0",
            "receipt_show_address": "1" if self.rec_show_address.isChecked() else "0",
        })
        QMessageBox.information(self, "Saved", "Tax & receipt settings saved.")

    # ---------------- Tables ----------------
    def _build_tables_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        form_row = QHBoxLayout()
        form_row.addWidget(QLabel("Table No:"))
        self.t_no = QLineEdit()
        self.t_no.setFixedWidth(120)
        form_row.addWidget(self.t_no)
        form_row.addWidget(QLabel("Seats:"))
        self.t_seats = QSpinBox()
        self.t_seats.setRange(1, 30)
        self.t_seats.setValue(2)
        self.t_seats.setFixedWidth(80)
        form_row.addWidget(self.t_seats)
        add = QPushButton("+  Add Table")
        add.setProperty("primary", True)
        add.clicked.connect(self._add_table)
        form_row.addWidget(add)
        form_row.addStretch()
        lay.addLayout(form_row)

        self.tables_table = QTableWidget(0, 4)
        self.tables_table.setHorizontalHeaderLabels(["ID", "Table No", "Seats", "Status"])
        self.tables_table.verticalHeader().setVisible(False)
        self.tables_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tables_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tables_table.setSelectionMode(QTableWidget.SingleSelection)
        self.tables_table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.tables_table, 1)

        row_btns = QHBoxLayout()
        edit = QPushButton("Edit")
        edit.clicked.connect(self._edit_table)
        delete = QPushButton("Delete")
        delete.setProperty("danger", True)
        delete.clicked.connect(self._delete_table)
        row_btns.addStretch()
        row_btns.addWidget(edit)
        row_btns.addWidget(delete)
        lay.addLayout(row_btns)
        self.refresh_tables()
        bind_table_keys(self.tables_table, on_enter=self._edit_table, on_delete=self._delete_table)
        return w

    def refresh_tables(self):
        tables = table_service.list_all()
        self.tables_table.setRowCount(len(tables))
        for i, t in enumerate(tables):
            self.tables_table.setItem(i, 0, QTableWidgetItem(str(t["id"])))
            self.tables_table.setItem(i, 1, QTableWidgetItem(t["table_no"]))
            self.tables_table.setItem(i, 2, QTableWidgetItem(str(t["seats"])))
            self.tables_table.setItem(i, 3, QTableWidgetItem(t["status"].upper()))
        self.tables_table.resizeColumnsToContents()

    def _selected_table(self):
        row = self.tables_table.currentRow()
        if row < 0:
            return None
        tables = table_service.list_all()
        return tables[row]

    def _add_table(self):
        no = self.t_no.text().strip()
        if not no:
            return
        try:
            table_service.add(no, self.t_seats.value())
            self.t_no.clear()
            self.refresh_tables()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def _edit_table(self):
        t = self._selected_table()
        if not t:
            return
        no, ok1 = QInputDialog.getText(self, "Edit Table", "Table No:", text=t["table_no"])
        if not ok1:
            return
        seats, ok2 = QInputDialog.getInt(self, "Edit Table", "Seats:", value=t["seats"], min=1, max=30)
        if not ok2:
            return
        try:
            table_service.update(t["id"], no.strip(), seats)
            self.refresh_tables()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def _delete_table(self):
        t = self._selected_table()
        if not t:
            return
        try:
            table_service.delete(t["id"])
            self.refresh_tables()
        except ValueError as e:
            QMessageBox.warning(self, "Cannot Delete", str(e))

    # ---------------- Staff ----------------
    def _build_staff_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        form_row = QHBoxLayout()
        form_row.addWidget(QLabel("Name:"))
        self.st_name = QLineEdit()
        self.st_name.setFixedWidth(160)
        form_row.addWidget(self.st_name)
        form_row.addWidget(QLabel("Role:"))
        self.st_role = QComboBox()
        self.st_role.addItems(["Waiter", "Captain", "Runner", "Rider"])
        form_row.addWidget(self.st_role)
        form_row.addWidget(QLabel("Phone:"))
        self.st_phone = QLineEdit()
        self.st_phone.setFixedWidth(140)
        form_row.addWidget(self.st_phone)
        add = QPushButton("+  Add Staff")
        add.setProperty("primary", True)
        add.clicked.connect(self._add_staff)
        form_row.addWidget(add)
        form_row.addStretch()
        lay.addLayout(form_row)

        self.staff_table = QTableWidget(0, 4)
        self.staff_table.setHorizontalHeaderLabels(["ID", "Name", "Role", "Phone"])
        self.staff_table.verticalHeader().setVisible(False)
        self.staff_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.staff_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.staff_table.setSelectionMode(QTableWidget.SingleSelection)
        self.staff_table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.staff_table, 1)

        row_btns = QHBoxLayout()
        edit = QPushButton("Edit")
        edit.clicked.connect(self._edit_staff)
        delete = QPushButton("Delete")
        delete.setProperty("danger", True)
        delete.clicked.connect(self._delete_staff)
        row_btns.addStretch()
        row_btns.addWidget(edit)
        row_btns.addWidget(delete)
        lay.addLayout(row_btns)
        self.refresh_staff()
        bind_table_keys(self.staff_table, on_enter=self._edit_staff, on_delete=self._delete_staff)
        return w

    def refresh_staff(self):
        staff = staff_service.list_all()
        self.staff_table.setRowCount(len(staff))
        for i, s in enumerate(staff):
            self.staff_table.setItem(i, 0, QTableWidgetItem(str(s["id"])))
            self.staff_table.setItem(i, 1, QTableWidgetItem(s["name"]))
            self.staff_table.setItem(i, 2, QTableWidgetItem(s["role"]))
            self.staff_table.setItem(i, 3, QTableWidgetItem(s["phone"] or ""))
        self.staff_table.resizeColumnsToContents()

    def _add_staff(self):
        if not self.st_name.text().strip():
            return
        staff_service.add(self.st_name.text().strip(), self.st_role.currentText(), self.st_phone.text().strip())
        self.st_name.clear()
        self.st_phone.clear()
        self.refresh_staff()

    def _edit_staff(self):
        row = self.staff_table.currentRow()
        if row < 0:
            return
        s = staff_service.list_all()[row]
        name, ok = QInputDialog.getText(self, "Edit Staff", "Name:", text=s["name"])
        if not ok:
            return
        staff_service.update(s["id"], name.strip(), s["role"], s["phone"] or "", True)
        self.refresh_staff()

    def _delete_staff(self):
        row = self.staff_table.currentRow()
        if row < 0:
            return
        s = staff_service.list_all()[row]
        if QMessageBox.question(self, "Delete", f"Delete staff {s['name']}?") == QMessageBox.Yes:
            staff_service.delete(s["id"])
            self.refresh_staff()

    # ---------------- Users ----------------
    def _build_users_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        form_row = QHBoxLayout()
        form_row.addWidget(QLabel("Username:"))
        self.u_user = QLineEdit()
        self.u_user.setFixedWidth(130)
        form_row.addWidget(self.u_user)
        form_row.addWidget(QLabel("Password:"))
        self.u_pass = QLineEdit()
        self.u_pass.setFixedWidth(130)
        self.u_pass.setEchoMode(QLineEdit.Password)
        form_row.addWidget(self.u_pass)
        form_row.addWidget(QLabel("Name:"))
        self.u_name = QLineEdit()
        self.u_name.setFixedWidth(150)
        form_row.addWidget(self.u_name)
        form_row.addWidget(QLabel("Role:"))
        self.u_role = QComboBox()
        self.u_role.addItems(ROLES)
        form_row.addWidget(self.u_role)
        add = QPushButton("+  Add User")
        add.setProperty("primary", True)
        add.clicked.connect(self._add_user)
        form_row.addWidget(add)
        form_row.addStretch()
        lay.addLayout(form_row)

        self.users_table = QTableWidget(0, 5)
        self.users_table.setHorizontalHeaderLabels(["ID", "Username", "Full Name", "Role", "Active"])
        self.users_table.verticalHeader().setVisible(False)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setSelectionMode(QTableWidget.SingleSelection)
        self.users_table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.users_table, 1)

        row_btns = QHBoxLayout()
        reset = QPushButton("Reset Password")
        reset.clicked.connect(self._reset_password)
        toggle = QPushButton("Enable / Disable")
        toggle.clicked.connect(self._toggle_user)
        delete = QPushButton("Delete")
        delete.setProperty("danger", True)
        delete.clicked.connect(self._delete_user)
        row_btns.addStretch()
        row_btns.addWidget(reset)
        row_btns.addWidget(toggle)
        row_btns.addWidget(delete)
        lay.addLayout(row_btns)
        self.refresh_users()
        bind_table_keys(self.users_table, on_delete=self._delete_user)
        return w

    def refresh_users(self):
        users = auth_service.list_users()
        self.users_table.setRowCount(len(users))
        for i, u in enumerate(users):
            self.users_table.setItem(i, 0, QTableWidgetItem(str(u["id"])))
            self.users_table.setItem(i, 1, QTableWidgetItem(u["username"]))
            self.users_table.setItem(i, 2, QTableWidgetItem(u["full_name"]))
            self.users_table.setItem(i, 3, QTableWidgetItem(u["role"]))
            self.users_table.setItem(i, 4, QTableWidgetItem("Yes" if u["is_active"] else "No"))
        self.users_table.resizeColumnsToContents()

    def _selected_user(self):
        row = self.users_table.currentRow()
        if row < 0:
            return None
        users = auth_service.list_users()
        return users[row]

    def _add_user(self):
        u = self.u_user.text().strip()
        p = self.u_pass.text()
        n = self.u_name.text().strip()
        if not u or not p:
            QMessageBox.warning(self, "Validation", "Username and password are required.")
            return
        try:
            auth_service.add_user(u, p, n or u, self.u_role.currentText())
            self.u_user.clear()
            self.u_pass.clear()
            self.u_name.clear()
            self.refresh_users()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def _reset_password(self):
        u = self._selected_user()
        if not u:
            return
        p, ok = QInputDialog.getText(self, "Reset Password", "New password:",
                                     echo=QLineEdit.Password)
        if ok and p:
            auth_service.set_password(u["id"], p)
            QMessageBox.information(self, "Done", "Password updated.")

    def _toggle_user(self):
        u = self._selected_user()
        if not u:
            return
        if u["role"] == "admin" and u["id"] == auth_service.current_user["id"]:
            QMessageBox.warning(self, "Warning", "You cannot disable your own account.")
            return
        auth_service.update_user(u["id"], u["full_name"], u["role"], not u["is_active"])
        self.refresh_users()

    def _delete_user(self):
        u = self._selected_user()
        if not u:
            return
        if u["role"] == "admin":
            QMessageBox.warning(self, "Warning", "Admin accounts cannot be deleted.")
            return
        if QMessageBox.question(self, "Delete", f"Delete user {u['username']}?") == QMessageBox.Yes:
            auth_service.delete_user(u["id"])
            self.refresh_users()

    # ---------------- Printing ----------------
    def _build_printing_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(14)

        card = QFrame()
        card.setProperty("card", True)
        form = QFormLayout(card)
        form.setContentsMargins(20, 18, 20, 18)
        form.setSpacing(12)

        self.p_printer = QComboBox()
        self.p_printer.setMinimumWidth(340)
        form.addRow("POS Printer", self.p_printer)
        self.p_printer.setToolTip(
            "Select the receipt printer. 'System Default' uses the Windows default printer.")

        row = QHBoxLayout()
        refresh = QPushButton("Refresh List")
        refresh.clicked.connect(self._refresh_printers)
        row.addWidget(refresh)
        row.addStretch()
        form.addRow("", row)

        self.p_encoding = QComboBox()
        self.p_encoding.addItems(["cp437", "cp850", "utf-8", "cp1252"])
        form.addRow("Character Encoding", self.p_encoding)

        self.p_cols = QSpinBox()
        self.p_cols.setRange(24, 48)
        self.p_cols.setValue(42)
        self.p_cols.setSuffix("  characters")
        form.addRow("Paper Width (chars)", self.p_cols)
        hint = QLabel("42 = 80mm thermal, 32 = 58mm thermal.")
        hint.setProperty("muted", True)
        form.addRow("", hint)

        self.p_cut = QComboBox()
        self.p_cut.addItem("Cut paper after receipt", "1")
        self.p_cut.addItem("No cut (leave paper uncut)", "0")
        form.addRow("After Printing", self.p_cut)
        lay.addWidget(card)

        test_card = QFrame()
        test_card.setProperty("card", True)
        tv = QVBoxLayout(test_card)
        tv.setContentsMargins(20, 18, 20, 18)
        tv.setSpacing(8)
        tv.addWidget(QLabel("Test Printer"))
        test_hint = QLabel("Prints a small test receipt to the selected printer.")
        test_hint.setProperty("muted", True)
        tv.addWidget(test_hint)
        self.btn_test = QPushButton("   Print Test Receipt")
        self.btn_test.setIcon(make_icon("print", "#ffffff", 24))
        self.btn_test.setIconSize(QSize(18, 18))
        self.btn_test.setProperty("primary", True)
        self.btn_test.clicked.connect(self._test_print)
        tv.addWidget(self.btn_test, alignment=Qt.AlignLeft)
        lay.addWidget(test_card)

        save = QPushButton("Save Printing Settings")
        save.setProperty("primary", True)
        save.clicked.connect(self._save_printing)
        lay.addWidget(save, alignment=Qt.AlignRight)
        lay.addStretch()
        return w

    def _refresh_printers(self):
        self._populate_printers(keep=settings_service.get("printer_name", "").strip())

    def _populate_printers(self, keep=""):
        self.p_printer.clear()
        self.p_printer.addItem("System Default", "")
        for name in list_printers():
            self.p_printer.addItem(name, name)
        idx = self.p_printer.findData(keep)
        self.p_printer.setCurrentIndex(idx if idx >= 0 else 0)

    def _save_printing(self):
        settings_service.set_many({
            "printer_name": self.p_printer.currentData() or "",
            "printer_encoding": self.p_encoding.currentText(),
            "printer_cols": str(self.p_cols.value()),
            "printer_cut": self.p_cut.currentData(),
        })
        QMessageBox.information(self, "Saved", "Printing settings saved.")

    def _test_print(self):
        self._save_printing()
        try:
            test_print()
            QMessageBox.information(self, "Test Print", "Test receipt sent to the printer.")
        except Exception as e:
            QMessageBox.critical(self, "Print Error", str(e))

    # ---------------- Backup / Restore ----------------
    def _build_backup_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(14)

        download = QFrame()
        download.setProperty("card", True)
        dv = QVBoxLayout(download)
        dv.setContentsMargins(20, 18, 20, 18)
        dv.setSpacing(8)
        dv.addWidget(QLabel("Backup Data"))
        d_hint = QLabel("Create a backup file of all your data (orders, products, staff, settings).")
        d_hint.setProperty("muted", True)
        d_hint.setWordWrap(True)
        dv.addWidget(d_hint)
        b_download = QPushButton("   Download Backup")
        b_download.setIcon(make_icon("download", "#ffffff", 24))
        b_download.setIconSize(QSize(18, 18))
        b_download.setProperty("primary", True)
        b_download.clicked.connect(self._download_backup)
        dv.addWidget(b_download, alignment=Qt.AlignLeft)
        lay.addWidget(download)

        restore = QFrame()
        restore.setProperty("card", True)
        rv = QVBoxLayout(restore)
        rv.setContentsMargins(20, 18, 20, 18)
        rv.setSpacing(8)
        rv.addWidget(QLabel("Restore Backup"))
        r_hint = QLabel("Replace the current data with a previously saved backup file. "
                        "You will be logged out and must sign in again.")
        r_hint.setProperty("muted", True)
        r_hint.setWordWrap(True)
        rv.addWidget(r_hint)
        b_apply = QPushButton("   Apply Backup File")
        b_apply.setIcon(make_icon("refresh", "#ffffff", 24))
        b_apply.setIconSize(QSize(18, 18))
        b_apply.setProperty("primary", True)
        b_apply.clicked.connect(self._apply_backup)
        rv.addWidget(b_apply, alignment=Qt.AlignLeft)
        lay.addWidget(restore)

        reset = QFrame()
        reset.setProperty("card", True)
        xv = QVBoxLayout(reset)
        xv.setContentsMargins(20, 18, 20, 18)
        xv.setSpacing(8)
        xv.addWidget(QLabel("Clear All Data"))
        x_hint = QLabel("Permanently delete ALL orders, products, staff, tables and settings. "
                        "The app will be reset to factory defaults. This cannot be undone.")
        x_hint.setProperty("muted", True)
        x_hint.setWordWrap(True)
        xv.addWidget(x_hint)
        b_clear = QPushButton("   Clear All Data")
        b_clear.setIcon(make_icon("trash", "#ffffff", 24))
        b_clear.setIconSize(QSize(18, 18))
        b_clear.setProperty("danger", True)
        b_clear.clicked.connect(self._clear_data)
        xv.addWidget(b_clear, alignment=Qt.AlignLeft)
        lay.addWidget(reset)

        lay.addStretch()
        return w

    def _download_backup(self):
        import datetime
        from app.config import DATA_DIR

        default = DATA_DIR / f"openpos_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Backup", str(default), "SQLite Database (*.db);;All Files (*)")
        if not path:
            return
        try:
            get_db().backup_to(path)
            QMessageBox.information(
                self, "Backup Created",
                f"Backup saved successfully.\n\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Backup Failed", str(e))

    def _apply_backup(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File", "", "SQLite Database (*.db);;All Files (*)")
        if not path:
            return
        resp = QMessageBox.warning(
            self, "Restore Backup",
            "This will replace ALL current data with the backup file.\n\n"
            "Continue?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        try:
            from app.database.db import Database
            Database.restore_from(path)
        except Exception as e:
            QMessageBox.critical(self, "Restore Failed", str(e))
            return
        QMessageBox.information(
            self, "Restored",
            "Backup restored successfully. You will be logged out.")
        self.data_changed.emit()

    def _clear_data(self):
        resp = QMessageBox.warning(
            self, "Clear All Data",
            "This will permanently delete ALL orders, products, staff, tables "
            "and settings.\n\n"
            "Type CLEAR to confirm.",
            QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
        if resp != QMessageBox.Ok:
            return
        text, ok = QInputDialog.getText(self, "Confirm Clear", "Type CLEAR to confirm:")
        if not ok or text.strip().upper() != "CLEAR":
            QMessageBox.information(self, "Cancelled", "Clear data cancelled.")
            return
        try:
            from app.database.db import Database
            Database.reset_all()
        except Exception as e:
            QMessageBox.critical(self, "Clear Failed", str(e))
            return
        QMessageBox.information(
            self, "Data Cleared",
            "All data has been cleared. The app has been reset to factory "
            "defaults (admin / admin123). You will be logged out.")
        self.data_changed.emit()

    # ---------------- load/save ----------------
    def reload(self):
        s = settings_service
        self.s_name.setText(s.get("store_name"))
        self.s_email.setText(s.get("store_email"))
        self.s_phone.setText(s.get("store_phone"))
        self.s_address.setText(s.get("store_address"))
        idx = self.s_currency.findText(s.get("currency", "Rs"))
        if idx >= 0:
            self.s_currency.setCurrentIndex(idx)
        logo = s.get("store_logo", "")
        self.logo_lbl.setText(f"✓ {logo}" if logo else "No logo uploaded")
        self.tax_name.setText(s.get("tax_name", "Sales Tax"))
        self.tax_rate.setValue(s.get_float("tax_rate", 0))
        self.delivery_charge.setValue(s.get_float("delivery_charge", 0))
        self.takeaway_charge.setValue(s.get_float("takeaway_charge", 0))
        self.rec_footer.setText(s.get("receipt_footer"))
        self.rec_show_logo.setChecked(s.get("receipt_show_logo", "1") == "1")
        self.rec_show_address.setChecked(s.get("receipt_show_address", "1") == "1")
        self.tax_dinein.setChecked(s.get("tax_dinein", "1") == "1")
        self.tax_takeaway.setChecked(s.get("tax_takeaway", "1") == "1")
        self.tax_delivery.setChecked(s.get("tax_delivery", "1") == "1")
        self._populate_printers(keep=s.get("printer_name", "").strip())
        enc = s.get("printer_encoding", "cp437")
        eidx = self.p_encoding.findText(enc)
        self.p_encoding.setCurrentIndex(eidx if eidx >= 0 else 0)
        try:
            self.p_cols.setValue(int(s.get("printer_cols", "42")))
        except (TypeError, ValueError):
            self.p_cols.setValue(42)
        cut = s.get("printer_cut", "1")
        cidx = self.p_cut.findData(cut)
        self.p_cut.setCurrentIndex(cidx if cidx >= 0 else 0)
        self.refresh_tables()
        self.refresh_staff()
        self.refresh_users()
