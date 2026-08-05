import sys
from pathlib import Path

APP_NAME = "Open POS"
APP_VERSION = "1.0.0"

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGOS_DIR = DATA_DIR / "logos"
BACKUPS_DIR = DATA_DIR / "backups"
DB_PATH = DATA_DIR / "openpos.db"

for _d in (DATA_DIR, LOGOS_DIR, BACKUPS_DIR):
    _d.mkdir(parents=True, exist_ok=True)
