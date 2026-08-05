import math

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

_ICON_COLOR = "#4b5563"


def _canvas(size, color, draw):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidthF(max(1.6, size / 13.0))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    draw(p, size)
    p.end()
    return QIcon(pm)


def _dashboard(p, s):
    d = s / 12.0
    for x, y in ((1, 1), (7, 1), (1, 7), (7, 7)):
        p.drawRoundedRect(QRectF(x * d, y * d, 4 * d, 4 * d), d, d)


def _bag(p, s):
    d = s / 24.0
    p.drawRoundedRect(QRectF(4 * d, 8 * d, 16 * d, 13 * d), 2 * d, 2 * d)
    p.drawArc(QRectF(7 * d, 2 * d, 10 * d, 10 * d), 0 * 16, -180 * 16)


def _table(p, s):
    d = s / 24.0
    p.drawLine(2 * d, 7 * d, 22 * d, 7 * d)
    p.drawLine(6 * d, 7 * d, 6 * d, 20 * d)
    p.drawLine(12 * d, 7 * d, 12 * d, 20 * d)
    p.drawLine(18 * d, 7 * d, 18 * d, 20 * d)
    p.drawLine(3 * d, 20 * d, 21 * d, 20 * d)


def _cup(p, s):
    d = s / 24.0
    path = QPainterPath()
    path.moveTo(6 * d, 7 * d)
    path.lineTo(18 * d, 7 * d)
    path.lineTo(16 * d, 20 * d)
    path.lineTo(8 * d, 20 * d)
    path.closeSubpath()
    p.drawPath(path)
    p.drawArc(QRectF(17 * d, 9 * d, 7 * d, 7 * d), 90 * 16, 180 * 16)
    p.drawLine(9 * d, 3 * d, 9 * d, 5 * d)
    p.drawLine(12 * d, 2 * d, 12 * d, 5 * d)
    p.drawLine(15 * d, 3 * d, 15 * d, 5 * d)


def _coins(p, s):
    d = s / 24.0
    p.drawEllipse(QRectF(5 * d, 12 * d, 10 * d, 10 * d))
    p.drawEllipse(QRectF(12 * d, 9 * d, 10 * d, 10 * d))
    p.drawEllipse(QRectF(8 * d, 15 * d, 10 * d, 10 * d))


def _chart(p, s):
    d = s / 24.0
    p.drawRoundedRect(QRectF(3 * d, 12 * d, 4.5 * d, 9 * d), 1 * d, 1 * d)
    p.drawRoundedRect(QRectF(10 * d, 5 * d, 4.5 * d, 16 * d), 1 * d, 1 * d)
    p.drawRoundedRect(QRectF(17 * d, 8 * d, 4.5 * d, 13 * d), 1 * d, 1 * d)


def _sliders(p, s):
    d = s / 24.0
    p.drawLine(3 * d, 7 * d, 21 * d, 7 * d)
    p.drawLine(3 * d, 12 * d, 21 * d, 12 * d)
    p.drawLine(3 * d, 17 * d, 21 * d, 17 * d)
    p.drawEllipse(QRectF(8 * d, 5 * d, 5 * d, 5 * d))
    p.drawEllipse(QRectF(15 * d, 10 * d, 5 * d, 5 * d))
    p.drawEllipse(QRectF(7 * d, 15 * d, 5 * d, 5 * d))


def _power(p, s):
    d = s / 24.0
    p.drawArc(QRectF(5 * d, 6 * d, 14 * d, 14 * d), 150 * 16, 240 * 16)
    p.drawLine(12 * d, 1.5 * d, 12 * d, 9 * d)


def _refresh(p, s):
    d = s / 24.0
    p.drawArc(QRectF(4 * d, 4 * d, 16 * d, 16 * d), 30 * 16, 290 * 16)
    a = math.radians(320)
    ex = 12 + 7.6 * math.cos(a)
    ey = 12 - 7.6 * math.sin(a)
    p.drawLine(ex * d, ey * d, (ex + 3) * d, (ey - 3.5) * d)
    p.drawLine(ex * d, ey * d, (ex + 4.5) * d, (ey + 0.5) * d)


def _plus(p, s):
    d = s / 24.0
    p.drawLine(12 * d, 4 * d, 12 * d, 20 * d)
    p.drawLine(4 * d, 12 * d, 20 * d, 12 * d)


def _minus(p, s):
    d = s / 24.0
    p.drawLine(4 * d, 12 * d, 20 * d, 12 * d)


def _close(p, s):
    d = s / 24.0
    p.drawLine(5 * d, 5 * d, 19 * d, 19 * d)
    p.drawLine(19 * d, 5 * d, 5 * d, 19 * d)


def _check(p, s):
    d = s / 24.0
    p.drawLine(4 * d, 13 * d, 10 * d, 18 * d)
    p.drawLine(10 * d, 18 * d, 20 * d, 6 * d)


def _tick(p, s):
    d = s / 24.0
    p.drawEllipse(QRectF(3 * d, 3 * d, 18 * d, 18 * d))
    p.drawLine(7 * d, 13 * d, 11 * d, 17 * d)
    p.drawLine(11 * d, 17 * d, 17 * d, 8 * d)


def _pencil(p, s):
    d = s / 24.0
    p.drawLine(4 * d, 20 * d, 18 * d, 6 * d)
    p.drawLine(18 * d, 6 * d, 20 * d, 4 * d)
    p.drawLine(2 * d, 22 * d, 5 * d, 19 * d)


def _trash(p, s):
    d = s / 24.0
    p.drawLine(4 * d, 6 * d, 20 * d, 6 * d)
    p.drawLine(6 * d, 6 * d, 6 * d, 20 * d)
    p.drawLine(18 * d, 6 * d, 18 * d, 20 * d)
    p.drawLine(6 * d, 20 * d, 18 * d, 20 * d)
    p.drawLine(9 * d, 6 * d, 9 * d, 3 * d)
    p.drawLine(15 * d, 6 * d, 15 * d, 3 * d)


def _search(p, s):
    d = s / 24.0
    p.drawEllipse(QRectF(4 * d, 4 * d, 11 * d, 11 * d))
    p.drawLine(13 * d, 13 * d, 20 * d, 20 * d)


def _print(p, s):
    d = s / 24.0
    p.drawRoundedRect(QRectF(5 * d, 3 * d, 14 * d, 8 * d), 1 * d, 1 * d)
    p.drawLine(8 * d, 5.5 * d, 16 * d, 5.5 * d)
    p.drawLine(8 * d, 8.5 * d, 16 * d, 8.5 * d)
    p.drawRoundedRect(QRectF(4 * d, 11 * d, 16 * d, 7 * d), 1 * d, 1 * d)
    p.drawRoundedRect(QRectF(7 * d, 18 * d, 10 * d, 3 * d), 1 * d, 1 * d)


def _user(p, s):
    d = s / 24.0
    p.drawEllipse(QRectF(8 * d, 3 * d, 8 * d, 8 * d))
    p.drawArc(QRectF(5 * d, 12 * d, 14 * d, 10 * d), 180 * 16, 180 * 16)


def _pin(p, s):
    d = s / 24.0
    p.drawArc(QRectF(7 * d, 3 * d, 10 * d, 10 * d), 0 * 16, 360 * 16)
    path = QPainterPath()
    path.moveTo(9 * d, 10 * d)
    path.lineTo(12 * d, 22 * d)
    path.lineTo(15 * d, 10 * d)
    p.drawPath(path)


def _note(p, s):
    d = s / 24.0
    p.drawRoundedRect(QRectF(4 * d, 3 * d, 16 * d, 18 * d), 2 * d, 2 * d)
    p.drawLine(8 * d, 8 * d, 16 * d, 8 * d)
    p.drawLine(8 * d, 12 * d, 16 * d, 12 * d)
    p.drawLine(8 * d, 16 * d, 13 * d, 16 * d)


def _phone(p, s):
    d = s / 24.0
    p.drawRoundedRect(QRectF(3 * d, 12 * d, 6 * d, 9 * d), 2 * d, 2 * d)
    p.drawRoundedRect(QRectF(15 * d, 3 * d, 6 * d, 9 * d), 2 * d, 2 * d)
    p.drawLine(9 * d, 15 * d, 15 * d, 9 * d)


def _home(p, s):
    d = s / 24.0
    p.drawLine(2 * d, 11 * d, 12 * d, 3 * d)
    p.drawLine(12 * d, 3 * d, 22 * d, 11 * d)
    p.drawLine(5 * d, 10 * d, 5 * d, 21 * d)
    p.drawLine(19 * d, 10 * d, 19 * d, 21 * d)
    p.drawLine(5 * d, 21 * d, 19 * d, 21 * d)
    p.drawRoundedRect(QRectF(9 * d, 14 * d, 6 * d, 7 * d), 1 * d, 1 * d)


def _box(p, s):
    d = s / 24.0
    p.drawRoundedRect(QRectF(5 * d, 10 * d, 14 * d, 11 * d), 1 * d, 1 * d)
    p.drawRoundedRect(QRectF(5 * d, 4 * d, 14 * d, 6 * d), 1 * d, 1 * d)
    p.drawLine(5 * d, 10 * d, 5 * d, 4 * d)
    p.drawLine(19 * d, 10 * d, 19 * d, 4 * d)
    p.drawLine(12 * d, 4 * d, 12 * d, 10 * d)


def _wallet(p, s):
    d = s / 24.0
    p.drawRoundedRect(QRectF(3 * d, 6 * d, 18 * d, 13 * d), 2 * d, 2 * d)
    p.drawRoundedRect(QRectF(14 * d, 10 * d, 7 * d, 5 * d), 1 * d, 1 * d)
    p.drawArc(QRectF(3 * d, 8 * d, 12 * d, 10 * d), 180 * 16, -180 * 16)


def _download(p, s):
    d = s / 24.0
    p.drawLine(12 * d, 3 * d, 12 * d, 13 * d)
    p.drawLine(7 * d, 9 * d, 12 * d, 14 * d)
    p.drawLine(17 * d, 9 * d, 12 * d, 14 * d)
    p.drawLine(4 * d, 19 * d, 20 * d, 19 * d)


def _panel(p, s):
    d = s / 24.0
    p.drawRoundedRect(QRectF(3 * d, 4 * d, 18 * d, 16 * d), 1.5 * d, 1.5 * d)
    p.drawLine(8 * d, 4 * d, 8 * d, 20 * d)
    p.drawLine(4 * d, 8 * d, 7 * d, 8 * d)
    p.drawLine(4 * d, 12 * d, 7 * d, 12 * d)
    p.drawLine(4 * d, 16 * d, 7 * d, 16 * d)


def _expand(p, s):
    d = s / 24.0
    p.drawLine(4 * d, 8 * d, 4 * d, 4 * d)
    p.drawLine(4 * d, 4 * d, 8 * d, 4 * d)
    p.drawLine(16 * d, 4 * d, 20 * d, 4 * d)
    p.drawLine(20 * d, 4 * d, 20 * d, 8 * d)
    p.drawLine(20 * d, 16 * d, 20 * d, 20 * d)
    p.drawLine(20 * d, 20 * d, 16 * d, 20 * d)
    p.drawLine(8 * d, 20 * d, 4 * d, 20 * d)
    p.drawLine(4 * d, 20 * d, 4 * d, 16 * d)


_DRAWERS = {
    "dashboard": _dashboard,
    "bag": _bag,
    "table": _table,
    "cup": _cup,
    "coins": _coins,
    "chart": _chart,
    "sliders": _sliders,
    "power": _power,
    "refresh": _refresh,
    "plus": _plus,
    "minus": _minus,
    "close": _close,
    "check": _check,
    "tick": _tick,
    "pencil": _pencil,
    "trash": _trash,
    "search": _search,
    "print": _print,
    "user": _user,
    "pin": _pin,
    "note": _note,
    "phone": _phone,
    "home": _home,
    "box": _box,
    "wallet": _wallet,
    "download": _download,
    "panel": _panel,
    "expand": _expand,
}

_cache = {}


def make_icon(name: str, color: str = _ICON_COLOR, size: int = 24) -> QIcon:
    drawer = _DRAWERS.get(name, _chart)
    key = (name, color, size)
    if key not in _cache:
        _cache[key] = _canvas(size, color, drawer)
    return _cache[key]


def icon_pixmap(name: str, color: str = _ICON_COLOR, size: int = 20):
    return make_icon(name, color, size * 2).pixmap(size, size)
