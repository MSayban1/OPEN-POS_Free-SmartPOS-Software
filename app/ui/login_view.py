from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QFrame, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox,
)

from app.services.auth_service import auth_service
from app.services.settings_service import settings_service
from app.ui.icons import icon_pixmap

ROLE_ICONS = {
    "admin": "Admin",
    "manager": "Manager",
    "cashier": "Cashier",
}


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login - Open POS")
        self.setFixedSize(420, 560)
        self.setModal(True)
        self.user = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        outer = QFrame()
        outer.setObjectName("LoginCard")
        outer.setStyleSheet(
            "QFrame#LoginCard { background: #ffffff; border-radius: 0px; }"
        )
        root.addWidget(outer)

        lay = QVBoxLayout(outer)
        lay.setContentsMargins(44, 40, 44, 36)
        lay.setSpacing(12)
        lay.addStretch(2)

        logo_path = settings_service.store_logo_path()
        logo_lbl = QLabel()
        logo_lbl.setAlignment(Qt.AlignCenter)
        logo_lbl.setFixedHeight(90)
        if logo_path:
            pm = QPixmap(logo_path)
            logo_lbl.setPixmap(pm.scaled(110, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_lbl.setPixmap(icon_pixmap("cup", "#4f46e5", 56))
        lay.addWidget(logo_lbl)

        store_lbl = QLabel(settings_service.get("store_name", "Open POS"))
        store_lbl.setAlignment(Qt.AlignCenter)
        store_lbl.setStyleSheet("font-size: 24px; font-weight: 800; color: #111827;")
        lay.addWidget(store_lbl)

        tagline = QLabel("Sign in to your Smart POS account")
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setProperty("muted", True)
        lay.addWidget(tagline)

        lay.addSpacing(10)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setFixedHeight(46)
        self.username.setStyleSheet(
            "QLineEdit { border: 1.5px solid #d1d5db; border-radius: 10px; padding: 10px 14px; font-size: 14px; }"
            "QLineEdit:focus { border: 1.5px solid #4f46e5; }"
        )
        lay.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setFixedHeight(46)
        self.password.setStyleSheet(
            "QLineEdit { border: 1.5px solid #d1d5db; border-radius: 10px; padding: 10px 14px; font-size: 14px; }"
            "QLineEdit:focus { border: 1.5px solid #4f46e5; }"
        )
        lay.addWidget(self.password)

        self.error_lbl = QLabel("")
        self.error_lbl.setStyleSheet("color: #ef4444; font-size: 13px;")
        self.error_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.error_lbl)

        self.btn = QPushButton("Sign In")
        self.btn.setStyleSheet(
            "QPushButton { background: #4f46e5; color: white; border: none; border-radius: 10px; "
            "padding: 12px; font-size: 15px; font-weight: 700; }"
            "QPushButton:hover { background: #4338ca; }"
        )
        lay.addWidget(self.btn)

        lay.addStretch(1)

        hint = QLabel("")
        hint.setAlignment(Qt.AlignCenter)
        hint.setProperty("muted", True)
        hint.setStyleSheet("font-size: 12px; color: #9ca3af;")
        lay.addWidget(hint)

        self.btn.clicked.connect(self._attempt_login)
        self.password.returnPressed.connect(self._attempt_login)
        self.username.returnPressed.connect(lambda: self.password.setFocus())

    def _attempt_login(self):
        self.error_lbl.setText("")
        ok, msg, user = auth_service.login(self.username.text(), self.password.text())
        if not ok:
            self.error_lbl.setText(msg)
            self.password.selectAll()
            self.password.setFocus()
            return
        self.user = user
        self.accept()

    def current_user(self):
        return self.user
