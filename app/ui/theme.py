APP_FONT = "Segoe UI"

QSS = """
* {
    font-family: "Segoe UI";
    font-size: 13px;
    color: #1f2937;
}
QMainWindow, QDialog {
    background: #f4f6fb;
}
#Sidebar {
    background: #ffffff;
    border-right: 1px solid #e5e7eb;
}
#SidebarHeader {
    background: #ffffff;
    border: none;
}
#SidebarHeader QLabel {
    color: #111827;
}
#NavButton {
    background: transparent;
    color: #4b5563;
    border: none;
    border-radius: 10px;
    padding: 12px 16px;
    text-align: left;
    font-size: 14px;
    font-weight: 600;
}
#NavButton:hover {
    background: #eef1f7;
    color: #111827;
}
#NavButton:checked {
    background: #4f46e5;
    color: #ffffff;
}
#PageTitle {
    font-size: 24px;
    font-weight: 700;
    color: #111827;
}
#PageSubtitle {
    font-size: 13px;
    color: #6b7280;
}
QLabel {
    color: #1f2937;
}
QLabel[muted="true"] {
    color: #6b7280;
}
QFrame[card="true"] {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
}
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
    background: #ffffff;
    border: 1.5px solid #d1d5db;
    border-radius: 9px;
    padding: 8px 11px;
    selection-background-color: #4f46e5;
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QComboBox:focus, QDateEdit:focus {
    border: 1.5px solid #4f46e5;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    selection-background-color: #eef2ff;
    selection-color: #111827;
    padding: 4px;
}
QPushButton {
    background: #ffffff;
    color: #1f2937;
    border: 1.5px solid #d1d5db;
    border-radius: 9px;
    padding: 9px 16px;
    font-weight: 600;
}
QPushButton:hover {
    border-color: #9ca3af;
    background: #f9fafb;
}
QPushButton:pressed {
    background: #eef1f7;
}
QPushButton[primary="true"] {
    background: #4f46e5;
    color: #ffffff;
    border: 1.5px solid #4f46e5;
}
QPushButton[primary="true"]:hover {
    background: #4338ca;
}
QPushButton[danger="true"] {
    background: #ef4444;
    color: #ffffff;
    border: 1.5px solid #ef4444;
}
QPushButton[danger="true"]:hover {
    background: #dc2626;
}
QPushButton[success="true"] {
    background: #10b981;
    color: #ffffff;
    border: 1.5px solid #10b981;
}
QPushButton[success="true"]:hover {
    background: #059669;
}
QPushButton[warning="true"] {
    background: #f59e0b;
    color: #ffffff;
    border: 1.5px solid #f59e0b;
}
QPushButton[warning="true"]:hover {
    background: #d97706;
}
QPushButton[ghost="true"] {
    background: transparent;
    border: none;
    color: #4b5563;
}
QPushButton[ghost="true"]:hover {
    background: #eef1f7;
}
QTableWidget, QTableView {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    gridline-color: #f1f3f7;
    selection-background-color: #eef2ff;
    selection-color: #111827;
}
QHeaderView::section {
    background: #f8fafc;
    border: none;
    border-bottom: 1px solid #e5e7eb;
    padding: 10px 8px;
    font-weight: 700;
    color: #4b5563;
}
QTableWidget::item {
    padding: 6px 4px;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}
QScrollBar::add-line, QScrollBar::sub-line {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: #cbd5e1;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #94a3b8;
}
QScrollBar::add-page, QScrollBar::sub-page {
    background: transparent;
}
QTabWidget::pane {
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    background: #ffffff;
    top: -1px;
}
QTabBar::tab {
    background: transparent;
    padding: 10px 22px;
    margin-right: 4px;
    border-top-left-radius: 9px;
    border-top-right-radius: 9px;
    font-weight: 600;
    color: #6b7280;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #4f46e5;
    border: 1px solid #e5e7eb;
    border-bottom: 2px solid #4f46e5;
}
QTabBar::tab:hover:!selected {
    color: #111827;
}
#CardTitle {
    font-size: 15px;
    font-weight: 700;
    color: #111827;
}
#StatValue {
    font-size: 26px;
    font-weight: 800;
    color: #111827;
}
#StatLabel {
    font-size: 12px;
    color: #6b7280;
    font-weight: 600;
}
#ProductCard {
    background: #ffffff;
    border: 1.5px solid #e5e7eb;
    border-radius: 12px;
}
#ProductCard:hover {
    border-color: #4f46e5;
    background: #fbfaff;
}
#ProductName {
    font-size: 13px;
    font-weight: 700;
    color: #111827;
}
#ProductPrice {
    font-size: 13px;
    font-weight: 800;
    color: #4f46e5;
}
#TableCard {
    border-radius: 16px;
    border: none;
}
#TableNo {
    font-size: 20px;
    font-weight: 800;
    color: #ffffff;
}
#TableInfo {
    font-size: 11px;
    color: rgba(255,255,255,0.92);
    font-weight: 600;
}
#Toast {
    background: #1f2937;
    border-radius: 10px;
}
#Toast QLabel {
    color: #ffffff;
}
#SearchBox {
    border-radius: 20px;
    padding: 10px 18px;
    border: 1.5px solid #d1d5db;
    background: #ffffff;
}
#ChipButton {
    background: #ffffff;
    border: 1.5px solid #e5e7eb;
    border-radius: 18px;
    padding: 6px 16px;
    font-weight: 600;
    color: #4b5563;
}
#ChipButton:checked {
    background: #4f46e5;
    color: #ffffff;
    border-color: #4f46e5;
}
#QtyBtn {
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    padding: 0;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 800;
}
#TotalsBox {
    background: #f8fafc;
    border-radius: 12px;
}
#MenuItemRow {
    background: #ffffff;
    border: 1px solid #f1f3f7;
    border-radius: 10px;
}
#SectionHeader {
    font-size: 14px;
    font-weight: 700;
    color: #111827;
}
QMessageBox {
    background: #ffffff;
}
QToolTip {
    background: #1f2937;
    color: #ffffff;
    border: none;
    padding: 6px;
    border-radius: 6px;
}
"""


def apply_theme(app):
    app.setStyleSheet(QSS)
