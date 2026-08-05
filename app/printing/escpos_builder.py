import struct
from pathlib import Path

INIT = b"\x1b@"
_ALIGN_LEFT = b"\x1ba\x00"
_ALIGN_CENTER = b"\x1ba\x01"
_ALIGN_RIGHT = b"\x1ba\x02"
BOLD_ON = b"\x1bE\x01"
BOLD_OFF = b"\x1bE\x00"
SIZE_DOUBLE = b"\x1d!\x14"
SIZE_NORMAL = b"\x1d!\x00"
CUT_PARTIAL = b"\x1dV\x01"
CUT_FULL = b"\x1dV\x00"

MAX_RASTER_WIDTH = 320


def _feed(n: int) -> bytes:
    return b"\x1bd" + bytes([n])


def raster_bytes_from_png(path, max_width=MAX_RASTER_WIDTH) -> bytes:
    """Render a monochrome ESC/POS raster (GS v 0) image block for a PNG."""
    try:
        from PIL import Image
    except ImportError:
        return b""
    try:
        img = Image.open(path)
    except Exception:
        return b""
    img = img.convert("L")
    if img.width > max_width:
        img = img.resize((max_width, int(img.height * max_width / img.width)))
    img = img.point(lambda p: 0 if p < 128 else 255, "1")
    data = img.tobytes()
    w = img.width
    h = img.height
    x_bytes = (w + 7) // 8
    packed = bytearray()
    for y in range(0, h, 8):
        for x in range(w):
            byte = 0
            for bit in range(8):
                if y + bit < h:
                    px = data[(y + bit) * w + x]
                    if px == 0:
                        byte |= 1 << (7 - bit)
            packed.append(byte)
    out = bytearray()
    out += b"\x1dv0\x00"
    out += struct.pack("<HH", x_bytes, (h + 7) // 8)
    out += packed
    return bytes(out)


class EscposBuilder:
    def __init__(self, cols: int = 42, encoding: str = "cp437"):
        self.cols = cols
        self.encoding = encoding
        self._raw_chunks = bytearray()

    def _add(self, text: str, align: str = "l", bold: bool = False, double: bool = False):
        cols = max(1, self.cols // 2) if double else self.cols
        for ln in _fit(str(text), cols):
            if align == "c":
                ln = ln.center(cols)
            elif align == "r":
                ln = ln.rjust(cols)
            else:
                ln = ln.ljust(cols)
            self._raw_chunks += _ALIGN_LEFT if align == "l" else (
                _ALIGN_CENTER if align == "c" else _ALIGN_RIGHT)
            self._raw_chunks += BOLD_ON if bold else BOLD_OFF
            self._raw_chunks += SIZE_DOUBLE if double else SIZE_NORMAL
            try:
                raw = ln.encode(self.encoding, errors="replace")
            except LookupError:
                raw = ln.encode("cp437", errors="replace")
            self._raw_chunks += raw + b"\n"
        return self

    def raw(self, data: bytes):
        self._raw_chunks += data
        return self

    def left(self, text: str, bold: bool = False):
        return self._add(text, "l", bold)

    def center(self, text: str, bold: bool = False, double: bool = False):
        return self._add(text, "c", bold, double)

    def right(self, text: str, bold: bool = False):
        return self._add(text, "r", bold)

    def blank(self, n: int = 1):
        for _ in range(max(0, n)):
            self._add("")
        return self

    def rule(self, char: str = "-", bold: bool = False):
        return self._add(char * self.cols, "l", bold)

    def kv(self, label, value, dotted: bool = True):
        label = str(label)
        value = str(value)
        fill = "." if dotted else " "
        if len(label) + 2 + len(value) > self.cols:
            value = value[: max(1, self.cols - len(label) - 2)]
        dots = max(0, self.cols - len(label) - len(value))
        return self._add(label + (fill * dots) + value)

    def items(self, rows, name_ratio: float = 0.56, qty_ratio: float = 0.16):
        name_w = max(1, int(self.cols * name_ratio))
        qty_w = max(1, int(self.cols * qty_ratio))
        price_w = max(1, self.cols - name_w - qty_w)
        self._add("ITEM".ljust(name_w) + "QTY".rjust(qty_w) + "PRICE".rjust(price_w), "l", True)
        self.rule("-")
        for it in rows:
            name = str(it.get("name", ""))
            qty = it.get("qty", 1)
            price = it.get("price", 0)
            try:
                qty_s = str(float(qty)).rstrip("0").rstrip(".") if float(qty) % 1 else str(int(float(qty)))
            except (TypeError, ValueError):
                qty_s = str(qty)
            price_s = f"{float(price):g}" if price != "" and price is not None else "0"
            lines = _fit(name, name_w)
            for i, ln in enumerate(lines):
                if i == 0:
                    self._add(ln.ljust(name_w) + qty_s.rjust(qty_w) + price_s.rjust(price_w))
                else:
                    self._add(ln.ljust(name_w))
        return self

    def summary(self, rows):
        for label, value, bold in rows:
            label = str(label)
            value = str(value)
            if len(label) + 2 + len(value) > self.cols:
                value = value[: max(1, self.cols - len(label) - 2)]
            self._add(label.ljust(self.cols - len(value)) + value, "l", bold)
        return self

    def build(self, cut: bool = True, feed: int = 3) -> bytes:
        out = bytearray(INIT)
        out += self._raw_chunks
        if cut:
            out += _feed(feed)
            out += CUT_PARTIAL
        return bytes(out)


def _fit(text: str, cols: int) -> list:
    lines = []
    for paragraph in str(text).split("\n"):
        words = paragraph.split(" ")
        cur = ""
        for w in words:
            t = (cur + " " + w).strip() if cur else w
            if len(t) <= cols:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                while len(w) > cols:
                    lines.append(w[:cols])
                    w = w[cols:]
                cur = w
        if cur or not paragraph:
            lines.append(cur)
    return lines or [""]
