from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtGui import QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMenu, QPlainTextEdit,
    QPushButton, QStackedWidget, QTextEdit, QVBoxLayout, QWidget,
)

from app.services.settings_service import settings_service
from app.ui.dashboard_view import DashboardView
from app.ui.dining_view import DiningView
from app.ui.expenses_view import ExpensesView
from app.ui.icons import icon_pixmap, make_icon
from app.ui.pos_view import PosView
from app.ui.products_view import ProductsView
from app.ui.reports_view import ReportsView
from app.ui.settings_view import SettingsView
from app.utils.crash_guard import get_logger

log = get_logger()

ROLE_LABELS = {"admin": "Administrator", "manager": "Manager", "cashier": "Cashier"}

NAV = [
    ("dashboard", "dashboard", "Dashboard"),
    ("pos", "bag", "Quick Sale"),
    ("dining", "table", "Dining"),
    ("products", "cup", "Products"),
    ("expenses", "coins", "Expenses"),
    ("reports", "chart", "Reports"),
    ("settings", "sliders", "Settings"),
]

ROLE_ACCESS = {
    "admin": {"dashboard", "pos", "dining", "products", "expenses", "reports", "settings"},
    "manager": {"dashboard", "pos", "dining", "products", "expenses", "reports"},
    "cashier": {"dashboard", "pos", "dining", "expenses"},
}


class MainWindow(QMainWindow):
    logout_requested = Signal()

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle(f"Open POS — {user['full_name']}")
        self.resize(1480, 920)
        self.setMinimumSize(1240, 760)
        self._sidebar_visible = True
        self.allowed = ROLE_ACCESS.get(self.user.get("role"), {"dashboard"})
        self._build()
        QShortcut(QKeySequence("F11"), self, activated=self._toggle_fullscreen)

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        central.installEventFilter(self)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---------------- Sidebar ----------------
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(230)
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(16, 20, 16, 16)
        sl.setSpacing(6)

        brand = QFrame()
        brand.setObjectName("SidebarHeader")
        bl = QHBoxLayout(brand)
        bl.setContentsMargins(6, 0, 6, 12)
        logo_path = settings_service.store_logo_path()
        icon = QLabel()
        icon.setFixedSize(40, 40)
        if logo_path:
            icon.setPixmap(QPixmap(logo_path).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            icon.setPixmap(icon_pixmap("cup", "#4f46e5", 32))
        icon.setAlignment(Qt.AlignCenter)
        bl.addWidget(icon)
        name = QLabel(settings_service.get("store_name", "Open POS"))
        name.setStyleSheet("font-size: 16px; font-weight: 800;")
        name.setWordWrap(True)
        bl.addWidget(name)
        sl.addWidget(brand)

        tools = QHBoxLayout()
        tools.addStretch()
        b_collapse = QPushButton()
        b_collapse.setObjectName("NavButton")
        b_collapse.setFixedSize(36, 36)
        b_collapse.setIcon(make_icon("panel", "#4b5563", 24))
        b_collapse.setIconSize(QSize(18, 18))
        b_collapse.setToolTip("Collapse sidebar")
        b_collapse.clicked.connect(lambda: self._collapse_sidebar())
        tools.addWidget(b_collapse)
        b_fullscreen = QPushButton()
        b_fullscreen.setObjectName("NavButton")
        b_fullscreen.setFixedSize(36, 36)
        b_fullscreen.setIcon(make_icon("expand", "#4b5563", 24))
        b_fullscreen.setIconSize(QSize(18, 18))
        b_fullscreen.setToolTip("Fullscreen (F11)")
        b_fullscreen.clicked.connect(lambda: self._toggle_fullscreen())
        tools.addWidget(b_fullscreen)
        sl.addLayout(tools)

        self.nav_buttons = {}
        self._nav_icons = {}
        for key, ico, label in NAV:
            btn = QPushButton(f"   {label}")
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setIconSize(QSize(20, 20))
            btn.setIcon(make_icon(ico, "#4b5563", 24))
            self._nav_icons[key] = ico
            btn.toggled.connect(lambda ch, k=key: self._nav_style(k, ch))
            btn.clicked.connect(lambda _=False, k=key: self.switch_page(k))
            sl.addWidget(btn)
            self.nav_buttons[key] = btn

        sl.addStretch()

        self.pages = QStackedWidget()
        self.views = {}
        for key, emoji, label in NAV:
            view = self._create_view(key)
            self.views[key] = view
            self.pages.addWidget(view)

        sl.addWidget(self._user_box())
        self.sidebar = sidebar
        root.addWidget(self.sidebar)

        # ---------------- Slim rail (when sidebar collapsed) ----------------
        rail = QFrame()
        rail.setObjectName("Sidebar")
        rail.setFixedWidth(64)
        rl = QVBoxLayout(rail)
        rl.setContentsMargins(10, 14, 10, 14)
        rl.setSpacing(6)
        b_expand = QPushButton()
        b_expand.setObjectName("NavButton")
        b_expand.setFixedSize(40, 40)
        b_expand.setIcon(make_icon("panel", "#4b5563", 24))
        b_expand.setIconSize(QSize(18, 18))
        b_expand.setToolTip("Expand sidebar")
        b_expand.clicked.connect(lambda: self._expand_sidebar())
        rl.addWidget(b_expand)
        self.rail_buttons = {}
        for key, ico, label in NAV:
            rb = QPushButton()
            rb.setObjectName("NavButton")
            rb.setCheckable(True)
            rb.setFixedSize(40, 40)
            rb.setIcon(make_icon(ico, "#4b5563", 24))
            rb.setIconSize(QSize(20, 20))
            rb.setToolTip(label)
            rb.toggled.connect(lambda ch, k=key: self._rail_style(k, ch))
            rb.clicked.connect(lambda _=False, k=key: self.switch_page(k))
            rl.addWidget(rb)
            self.rail_buttons[key] = rb
        rl.addStretch()
        self.rail = rail
        self.rail.setVisible(False)
        root.addWidget(self.rail)
        root.addWidget(self.pages, 1)

        self.nav_buttons["dashboard"].setChecked(True)
        self.rail_buttons["dashboard"].setChecked(True)
        self.pages.setCurrentWidget(self.views["dashboard"])

        for key, btn in self.nav_buttons.items():
            btn.setVisible(key in self.allowed)
        for key, rb in self.rail_buttons.items():
            rb.setVisible(key in self.allowed)
        first = next(k for k, _, _ in NAV if k in self.allowed)
        self.nav_buttons[first].setChecked(True)
        self.rail_buttons[first].setChecked(True)
        self.pages.setCurrentWidget(self.views[first])

    def _create_view(self, key):
        if key == "dashboard":
            return DashboardView()
        if key == "pos":
            return PosView()
        if key == "dining":
            return DiningView()
        if key == "products":
            return ProductsView()
        if key == "expenses":
            return ExpensesView()
        if key == "reports":
            return ReportsView()
        if key == "settings":
            v = SettingsView()
            v.reload()
            v.data_changed.connect(self.logout_requested)
            return v
        return QWidget()

    def _nav_style(self, key, checked):
        ico = self._nav_icons.get(key)
        if not ico:
            return
        color = "#ffffff" if checked else "#4b5563"
        self.nav_buttons[key].setIcon(make_icon(ico, color, 24))

    def _rail_style(self, key, checked):
        ico = self._nav_icons.get(key)
        if not ico:
            return
        color = "#ffffff" if checked else "#4b5563"
        self.rail_buttons[key].setIcon(make_icon(ico, color, 24))

    def _collapse_sidebar(self):
        self._sidebar_visible = False
        self.sidebar.setVisible(False)
        self.rail.setVisible(True)

    def _expand_sidebar(self):
        self._sidebar_visible = True
        self.rail.setVisible(False)
        self.sidebar.setVisible(True)

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _user_box(self):
        box = QFrame()
        box.setObjectName("SidebarHeader")
        box.setStyleSheet(
            "QFrame#SidebarHeader { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 14px; }"
        )
        lay = QVBoxLayout(box)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(2)
        who = QLabel(self.user["full_name"])
        who.setStyleSheet("font-weight: 800; color: #111827;")
        role = QLabel(ROLE_LABELS.get(self.user["role"], self.user["role"]))
        role.setStyleSheet("color: #6b7280; font-size: 12px;")
        lay.addWidget(who)
        lay.addWidget(role)
        logout = QPushButton("   Logout")
        logout.setIcon(make_icon("power", "#dc2626", 24))
        logout.setIconSize(QSize(18, 18))
        logout.setStyleSheet(
            "QPushButton { background: #fee2e2; color: #dc2626; border: none; border-radius: 9px; padding: 8px; font-weight: 700; }"
            "QPushButton:hover { background: #fecaca; }"
        )
        logout.clicked.connect(self.logout_requested)
        lay.addWidget(logout)
        return box

    def _safe_reload(self, view, method):
        fn = getattr(view, method, None)
        if fn is None:
            return
        try:
            fn()
        except Exception:
            log.exception("Error in %s.%s", type(view).__name__, method)
            self.statusBar().showMessage(
                "Something went wrong while loading this page. See logs for details.", 6000
            )

    def switch_page(self, key):
        if key not in self.allowed:
            return
        self.pages.setCurrentWidget(self.views[key])
        for k, b in self.nav_buttons.items():
            b.setChecked(k == key)
        for k, b in self.rail_buttons.items():
            b.setChecked(k == key)
        view = self.views[key]
        self._safe_reload(view, "refresh")
        self._safe_reload(view, "reload")

    def refresh_all(self):
        for view in self.views.values():
            self._safe_reload(view, "refresh")
            self._safe_reload(view, "reload")

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ContextMenu and not isinstance(
                obj, (QLineEdit, QTextEdit, QPlainTextEdit)):
            self._show_refresh_menu(event.globalPos())
            return True
        return super().eventFilter(obj, event)

    def _show_refresh_menu(self, pos):
        menu = QMenu(self)
        act = menu.addAction(make_icon("refresh", "#4f46e5", 24), "  Refresh")
        act.setToolTip("Reload all pages and settings")
        act.triggered.connect(self.refresh_all)
        menu.exec(pos)
