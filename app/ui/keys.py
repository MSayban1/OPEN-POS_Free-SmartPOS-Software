from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut


def bind_table_keys(widget, on_enter=None, on_delete=None):
    """Bind Enter -> edit and Delete -> delete on a table/list.

    Uses WidgetShortcut context so the shortcuts only fire when `widget`
    (or a child, e.g. the viewport) has focus. Arrow keys are already
    handled natively by Qt's table/list widgets.
    """
    if on_enter:
        for key in (Qt.Key_Return, Qt.Key_Enter):
            sc = QShortcut(QKeySequence(key), widget)
            sc.setContext(Qt.WidgetShortcut)
            sc.activated.connect(on_enter)
    if on_delete:
        sc = QShortcut(QKeySequence(Qt.Key_Delete), widget)
        sc.setContext(Qt.WidgetShortcut)
        sc.activated.connect(on_delete)
