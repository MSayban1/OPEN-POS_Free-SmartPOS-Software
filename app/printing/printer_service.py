import datetime

from app.printing.escpos_builder import EscposBuilder, raster_bytes_from_png
from app.services.settings_service import settings_service
from app.utils.helpers import fmt_money

BRANDING_LINE = "Software by Muhammad Sayban | Saban Productions"


class NoPrinterError(RuntimeError):
    pass


def list_printers() -> list:
    try:
        import win32print
    except ImportError:
        return []
    names = set()
    flags = getattr(win32print, "PRINTER_ENUM_LOCAL", 0) | getattr(
        win32print, "PRINTER_ENUM_CONNECTIONS", 0)
    for _, _, name, _ in win32print.EnumPrinters(flags):
        names.add(name)
    return sorted(names)


def _configured_printer() -> str | None:
    name = settings_service.get("printer_name", "").strip()
    if name:
        return name
    try:
        import win32print
        return win32print.GetDefaultPrinter()
    except Exception:
        return None


def _encoding() -> str:
    enc = settings_service.get("printer_encoding", "cp437").strip() or "cp437"
    return enc


def _cols() -> int:
    try:
        return max(16, min(64, int(settings_service.get("printer_cols", "42"))))
    except (TypeError, ValueError):
        return 42


def _cut_enabled() -> bool:
    return settings_service.get("printer_cut", "1") != "0"


def send_raw(data: bytes, printer: str | None = None) -> None:
    name = printer or _configured_printer()
    if not name:
        raise NoPrinterError(
            "No printer is available. Connect a POS printer and select it "
            "in Settings -> Printing."
        )
    try:
        import win32print
    except ImportError:
        raise NoPrinterError("win32print is not available on this system.") from None
    available = list_printers()
    if available and name not in available:
        raise NoPrinterError(
            f"Printer '{name}' is not connected/available. Check it is powered on, "
            "then select it in Settings -> Printing."
        )
    try:
        hprinter = win32print.OpenPrinter(name)
    except Exception as e:
        raise NoPrinterError(f"Cannot open printer '{name}': {e}") from e
    try:
        win32print.StartDocPrinter(hprinter, 1, ("Receipt", None, "RAW"))
        try:
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, data)
            win32print.EndPagePrinter(hprinter)
        finally:
            win32print.EndDocPrinter(hprinter)
    finally:
        win32print.ClosePrinter(hprinter)


def check_printer_connected(printer: str | None = None) -> str:
    """Return the printer name that would be used, or raise NoPrinterError if no
    POS printer is connected/available. Performs no printing."""
    name = printer or _configured_printer()
    if not name:
        raise NoPrinterError(
            "No POS printer is connected.\n\n"
            "Please connect a thermal/receipt printer to this computer, "
            "power it on, and select it in Settings -> Printing."
        )
    try:
        import win32print
    except ImportError:
        raise NoPrinterError(
            "This system cannot access the printer. Make sure the POS "
            "printer is connected and this app is running on Windows."
        ) from None
    available = list_printers()
    if available and name not in available:
        raise NoPrinterError(
            f"Printer '{name}' is not connected.\n\n"
            "Check that the printer is powered on and connected to this "
            "computer, then select it in Settings -> Printing."
        )
    return name


def print_or_error(data: bytes, parent=None) -> bool:
    """Print `data` if a POS printer is connected; otherwise show an error popup.
    Returns True on success, False (and shows a popup) if no printer."""
    from PySide6.QtWidgets import QMessageBox

    try:
        check_printer_connected()
        send_raw(data)
        return True
    except NoPrinterError as e:
        QMessageBox.critical(parent, "Printer Not Connected", str(e))
        return False
    except Exception as e:
        QMessageBox.critical(parent, "Print Error", str(e))
        return False



def _as_dict(row):
    return dict(row) if hasattr(row, "keys") else row


def _branding(b: EscposBuilder):
    b.center(BRANDING_LINE)


def _store_header(b: EscposBuilder, show_contact=True):
    settings = settings_service
    if settings.get("receipt_show_logo", "1") == "1":
        logo = settings.store_logo_path()
        if logo:
            try:
                data = raster_bytes_from_png(logo)
                if data:
                    b.raw(data).blank(1)
            except Exception:
                pass
    b.center(settings.get("store_name", "Open POS"), bold=True, double=True)
    if show_contact:
        for key in ("store_email", "store_phone", "store_address"):
            val = settings.get(key, "").strip()
            if val:
                b.center(val)
    b.rule()


def _items_for(order):
    from app.services.order_service import order_service
    return [dict(i) for i in order_service.get_items(order["id"])]


def _info_lines(order, cashier_label=True, show_day=True, show_waiter=True, show_rider=False):
    created = str(order["created_at"])
    try:
        dt = datetime.datetime.strptime(created, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        dt = datetime.datetime.now()
    lines = [("Order No.", str(order["order_number"]))]
    if order.get("table_no"):
        lines.append(("Table", f"{order['table_no']}   Seats: {order.get('seats', '-')}"))
    if show_waiter and order.get("waiter_name"):
        lines.append(("Waiter", order["waiter_name"]))
    if show_rider and order.get("rider_name"):
        lines.append(("Rider", order["rider_name"]))
    if cashier_label and order.get("cashier_name"):
        lines.append(("Cashier", order["cashier_name"]))
    date_str = dt.strftime("%d-%b-%Y")
    if show_day:
        date_str += f"  ({dt.strftime('%A')})"
    lines.append(("Date", date_str))
    lines.append(("Time", dt.strftime("%I:%M %p")))
    return lines


def _order_type_label(order):
    return {"dine-in": "DINE-IN", "takeaway": "TAKE-AWAY", "delivery": "DELIVERY"}.get(
        order.get("order_type", "dine-in"), "DINE-IN"
    )


def _items_rows(order, show_price=True):
    items = _items_for(order)
    return [
        {"name": it["name"], "qty": it["qty"], "price": it["price"] if show_price else ""}
        for it in items
    ]


def _summary_rows(order):
    currency = settings_service.get("currency", "Rs")
    sub = float(order["subtotal"] or 0)
    disc = float(order["discount"] or 0)
    tax = float(order["tax"] or 0)
    charge = float(order.get("service_charge") or 0)
    total = float(order["total"] or 0)
    rows = [("Subtotal", fmt_money(sub, currency), False)]
    if disc > 0:
        rows.append(("Discount", f"- {fmt_money(disc, currency)}", False))
    if tax > 0:
        rows.append((settings_service.get("tax_name", "Tax"), fmt_money(tax, currency), False))
    if charge > 0:
        label = "Delivery Charge" if order.get("order_type") == "delivery" else "Takeaway Charge"
        rows.append((label, fmt_money(charge, currency), False))
    rows.append(("TOTAL", fmt_money(total, currency), True))
    return rows


def _new_builder() -> EscposBuilder:
    return EscposBuilder(cols=_cols(), encoding=_encoding())


def print_kot(order) -> bytes:
    order = _as_dict(order)
    b = _new_builder()
    b.center("KOT", bold=True, double=True)
    b.center(_order_type_label(order), bold=True)
    b.blank()
    for label, value in _info_lines(order, cashier_label=False, show_day=True, show_waiter=True):
        b.kv(label, value)
    b.rule()
    kot_items = []
    for it in _items_for(order):
        name = it["name"]
        if it.get("instructions"):
            name += "  *"
        kot_items.append({"name": name, "qty": it["qty"], "price": it["price"]})
    b.items(kot_items)
    b.blank()
    if order.get("instructions"):
        b.left("Order Note:", bold=True)
        b.left(order["instructions"])
    item_notes = [it for it in _items_for(order) if it.get("instructions")]
    if item_notes:
        b.rule("-")
        for it in item_notes:
            b.left(f"{it['name']}  *  {it['instructions']}")
    b.rule()
    b.center("THANK YOU", bold=True)
    _branding(b)
    data = b.build(cut=_cut_enabled())
    send_raw(data)
    return data


def print_request_bill(order) -> bytes:
    order = _as_dict(order)
    settings = settings_service
    b = _new_builder()
    _store_header(b, show_contact=True)
    b.center("BILL", bold=True, double=True)
    for label, value in _info_lines(order, cashier_label=True, show_day=True, show_waiter=False):
        b.kv(label, value)
    b.rule()
    b.items(_items_rows(order, show_price=True))
    b.rule()
    b.summary(_summary_rows(order))
    b.blank()
    footer = settings.get("receipt_footer", "").strip()
    if footer:
        b.center(footer)
    _branding(b)
    data = b.build(cut=_cut_enabled())
    send_raw(data)
    return data


def print_rider_bill(order) -> bytes:
    order = _as_dict(order)
    b = _new_builder()
    b.center("RIDER COPY", bold=True, double=True)
    b.center("DELIVERY ORDER", bold=True)
    b.blank()
    b.kv("Order No.", str(order["order_number"]))
    if order.get("rider_name"):
        b.kv("Rider", order["rider_name"])
    b.rule()
    b.kv("Customer", order.get("customer_name") or "-")
    if order.get("customer_phone"):
        b.kv("Phone", order["customer_phone"])
    if order.get("customer_address"):
        b.left("Address:", bold=True)
        b.left(order["customer_address"])
    b.rule()
    b.items(_items_rows(order, show_price=True))
    b.rule()
    b.center("Deliver at your earliest!", bold=True)
    _branding(b)
    data = b.build(cut=_cut_enabled())
    send_raw(data)
    return data


def print_final_bill(order) -> bytes:
    order = _as_dict(order)
    settings = settings_service
    b = _new_builder()
    _store_header(b, show_contact=True)
    b.center("FINAL BILL", bold=True, double=True)
    b.center(_order_type_label(order), bold=True)
    b.blank()
    for label, value in _info_lines(order, cashier_label=True, show_day=True, show_waiter=True, show_rider=True):
        b.kv(label, value)
    if order.get("payment_method"):
        b.kv("Payment", order["payment_method"])
    b.rule()
    b.items(_items_rows(order, show_price=True))
    b.rule()
    b.summary(_summary_rows(order))
    b.blank()
    b.rule("-")
    b.center("Thank you for your visit!", bold=True)
    footer = settings.get("receipt_footer", "").strip()
    if footer:
        b.center(footer)
    _branding(b)
    data = b.build(cut=_cut_enabled())
    send_raw(data)
    return data


def test_print() -> bytes:
    settings = settings_service
    b = _new_builder()
    _store_header(b, show_contact=True)
    b.center("TEST PRINT", bold=True, double=True)
    b.blank()
    b.kv("Store", settings.get("store_name", "Open POS"))
    b.kv("Currency", settings.get("currency", "Rs"))
    b.kv("Date", datetime.datetime.now().strftime("%d-%b-%Y"))
    b.kv("Time", datetime.datetime.now().strftime("%I:%M %p"))
    b.rule()
    b.items([{"name": "Test Item 1", "qty": 2, "price": 50},
             {"name": "Test Item 2", "qty": 1, "price": 100}])
    b.rule()
    b.summary([("Subtotal", fmt_money(200, settings.get("currency", "Rs")), False),
               ("TOTAL", fmt_money(200, settings.get("currency", "Rs")), True)])
    b.blank()
    b.center("Printer connected OK", bold=True)
    data = b.build(cut=_cut_enabled())
    send_raw(data)
    return data
