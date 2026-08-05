import datetime

from PySide6.QtCore import QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

PALETTE = [
    "#4f46e5", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
    "#ec4899", "#14b8a6", "#3b82f6", "#f97316", "#84cc16",
]

MUTED = "#6b7280"
GRID = "#e5e7eb"
DARK = "#374151"


def _fmt(v):
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    return f"{v:,.2f}"


class ChartBase(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []
        self.setMinimumHeight(250)

    def set_data(self, data):
        self.data = data or []
        self.update()


class BarChart(ChartBase):
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        if not self.data:
            p.setPen(QColor("#9ca3af"))
            p.drawText(self.rect(), Qt.AlignCenter, "No data")
            return

        margin_left, margin_right, margin_top, margin_bottom = 56, 16, 24, 34
        chart_w = w - margin_left - margin_right
        chart_h = h - margin_top - margin_bottom
        max_val = max(d["value"] for d in self.data) or 1

        p.setPen(QColor(GRID))
        for i in range(5):
            y = margin_top + chart_h * i / 4
            p.drawLine(margin_left, int(y), w - margin_right, int(y))

        n = len(self.data)
        slot = chart_w / n
        bar_w = min(slot * 0.5, 52)

        for i, d in enumerate(self.data):
            cx = margin_left + slot * i + slot / 2
            bh = (d["value"] / max_val) * (chart_h - 8)
            color = QColor(d.get("color", PALETTE[0]))
            p.setPen(Qt.NoPen)
            p.setBrush(color)
            rect = QRectF(cx - bar_w / 2, margin_top + chart_h - bh, bar_w, bh)
            p.drawRoundedRect(rect, 6, 6)

            f = QFont()
            f.setPointSize(8)
            f.setBold(True)
            p.setFont(f)
            p.setPen(QColor(DARK))
            p.drawText(
                QRect(int(cx - bar_w), int(margin_top + chart_h - bh - 20), int(bar_w * 2), 16),
                Qt.AlignCenter, _fmt(d["value"]))

            p.setPen(QColor(MUTED))
            f2 = QFont()
            f2.setPointSize(8)
            p.setFont(f2)
            p.drawText(
                QRect(int(cx - slot / 2), margin_top + chart_h + 8, int(slot), 16),
                Qt.AlignCenter, d["label"])

        p.end()


class LineChart(ChartBase):
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        if not self.data:
            p.setPen(QColor("#9ca3af"))
            p.drawText(self.rect(), Qt.AlignCenter, "No data")
            return

        margin_left, margin_right, margin_top, margin_bottom = 56, 16, 24, 34
        chart_w = w - margin_left - margin_right
        chart_h = h - margin_top - margin_bottom
        max_val = max(d["value"] for d in self.data) or 1

        p.setPen(QColor(GRID))
        for i in range(5):
            y = margin_top + chart_h * i / 4
            p.drawLine(margin_left, int(y), w - margin_right, int(y))

        n = len(self.data)
        if n == 1:
            xs = [margin_left + chart_w / 2]
        else:
            xs = [margin_left + chart_w * i / (n - 1) for i in range(n)]
        ys = [margin_top + chart_h - (d["value"] / max_val) * (chart_h - 8) for d in self.data]

        points = [QPointF(x, y) for x, y in zip(xs, ys)]
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#4f46e5"))
        for x, y, d in zip(xs, ys, self.data):
            color = QColor(d.get("color", "#4f46e5"))
            p.setBrush(color)
            p.drawEllipse(QRectF(x - 4, y - 4, 8, 8))

        path = QPainterPath(points[0])
        for x, y in zip(xs[1:], ys[1:]):
            path.lineTo(x, y)
        p.setPen(QColor("#4f46e5"))
        p.setBrush(Qt.NoBrush)
        p.drawPath(path)

        f = QFont()
        f.setPointSize(8)
        p.setFont(f)
        for x, y, d in zip(xs, ys, self.data):
            p.setPen(QColor(DARK))
            p.setBrush(QColor("#ffffff"))
            label = _fmt(d["value"])
            r = QRect(int(x - 40), int(y - 24), 80, 16)
            p.drawText(r, Qt.AlignCenter, label)
            p.setPen(QColor(MUTED))
            p.drawText(
                QRect(int(x - 60), margin_top + chart_h + 8, 120, 16),
                Qt.AlignCenter, d["label"])

        p.end()


class PieChart(ChartBase):
    def set_data(self, data):
        super().set_data(data)
        self.setMinimumHeight(max(250, len(self.data) * 24 + 36))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        total = sum(d["value"] for d in self.data) or 1
        if not self.data:
            p.setPen(QColor("#9ca3af"))
            p.drawText(self.rect(), Qt.AlignCenter, "No data")
            return

        legend_w = max(int(w * 0.4), 130)
        side = min(w - legend_w - 16, h - 16)
        size = max(side, 60)
        cx = (w - legend_w) / 2
        cy = h / 2
        rect = QRectF(cx - size / 2, cy - size / 2, size, size)

        start = 90 * 16
        for i, d in enumerate(self.data):
            span = -(d["value"] / total) * 360 * 16
            color = QColor(d.get("color", PALETTE[i % len(PALETTE)]))
            p.setPen(QColor("#ffffff"))
            p.setPen(QPen(QColor("#ffffff"), 2))
            p.setBrush(color)
            p.drawPie(rect, start, int(span))
            start += int(span)

        p.setBrush(QColor("#ffffff"))
        inner = QRectF(rect.center().x() - size * 0.28, rect.center().y() - size * 0.28, size * 0.56, size * 0.56)
        p.drawEllipse(inner)

        f = QFont()
        f.setPointSize(9)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor(DARK))
        p.drawText(inner, Qt.AlignCenter, f"{_fmt(total)}")

        legend_x = w - legend_w + 8
        f2 = QFont()
        f2.setPointSize(9)
        p.setFont(f2)
        y = h / 2 - (len(self.data) * 22) / 2
        for i, d in enumerate(self.data):
            color = QColor(d.get("color", PALETTE[i % len(PALETTE)]))
            p.setBrush(color)
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(QRectF(legend_x, y + 2, 12, 12), 3, 3)
            p.setPen(QColor(DARK))
            pct = (d["value"] / total) * 100 if total else 0
            label = f"{d['label']}  {pct:.0f}%"
            p.drawText(QRect(int(legend_x + 18), int(y - 2), 160, 18), Qt.AlignLeft | Qt.AlignVCenter, label)
            y += 22

        p.end()


class HBarChart(ChartBase):
    def set_data(self, data):
        super().set_data(data)
        self.setMinimumHeight(max(250, len(self.data) * 34 + 28))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        if not self.data:
            p.setPen(QColor("#9ca3af"))
            p.drawText(self.rect(), Qt.AlignCenter, "No data")
            return

        margin_left, margin_right, margin_top, margin_bottom = 140, 64, 12, 12
        chart_w = w - margin_left - margin_right
        chart_h = h - margin_top - margin_bottom
        max_val = max(d["value"] for d in self.data) or 1
        n = len(self.data)
        slot = chart_h / n
        bar_h = min(slot * 0.55, 22)

        for i, d in enumerate(self.data):
            y = margin_top + slot * i + (slot - bar_h) / 2
            bw = (d["value"] / max_val) * chart_w
            color = QColor(d.get("color", PALETTE[0]))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#eef2ff"))
            p.drawRoundedRect(QRectF(margin_left, y, chart_w, bar_h), 5, 5)
            p.setBrush(color)
            p.drawRoundedRect(QRectF(margin_left, y, bw, bar_h), 5, 5)

            f = QFont()
            f.setPointSize(9)
            p.setFont(f)
            p.setPen(QColor(DARK))
            p.drawText(QRect(0, int(y), margin_left - 8, int(bar_h)), Qt.AlignRight | Qt.AlignVCenter, d["label"])
            p.setPen(QColor(MUTED))
            p.drawText(
                QRect(int(margin_left + bw + 8), int(y), 60, int(bar_h)),
                Qt.AlignLeft | Qt.AlignVCenter, _fmt(d["value"]))

        p.end()
