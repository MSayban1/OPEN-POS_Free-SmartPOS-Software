import logging
import sys
import threading
import traceback

from app.config import BASE_DIR

_LOG_DIR = BASE_DIR / "data" / "logs"
_LOG_FILE = _LOG_DIR / "app.log"


def setup_logging():
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("openpos")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    fh.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(fh)
    logger.propagate = False
    return logger


def get_logger(name="openpos"):
    return logging.getLogger(name)


def _report(exc_type, exc, tb):
    logger = setup_logging()
    text = "".join(traceback.format_exception(exc_type, exc, tb))
    logger.error("Unhandled exception:\n%s", text)
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox

        if QApplication.instance():
            QMessageBox.critical(
                None,
                "Unexpected Error",
                "An unexpected error occurred.\n\n%s: %s\n\nDetails saved to:\n%s"
                % (exc_type.__name__, exc, _LOG_FILE),
            )
    except Exception:
        pass


def install():
    setup_logging()

    def hook(exc_type, exc, tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return
        _report(exc_type, exc, tb)

    sys.excepthook = hook
    if hasattr(threading, "excepthook"):
        threading.excepthook = hook
