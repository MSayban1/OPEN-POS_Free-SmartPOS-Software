<div align="center">

# ☕ Open POS

**A modern, offline, open-source Point of Sale system for cafes and restaurants.**

Built with **Python** and **Qt (PySide6)** · Runs 100% locally · No internet required · No subscription fees

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-Qt6-41CD52?style=flat&logo=qt&logoColor=white)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=flat&logo=sqlite&logoColor=white)
![Windows](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat&logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-Public%20Domain-green?style=flat)
![Version](https://img.shields.io/badge/Version-1.0.0-blue?style=flat)

**Created by [Muhammad Sayban](https://github.com/) | Saban Productions**

</div>

---

## 📖 Table of Contents

- [Introduction](#-introduction)
- [Features](#-features)
- [Tech Stack & Libraries](#-tech-stack--libraries)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Quick Start (First Run)](#-quick-start-first-run)
- [Usage Guide](#-usage-guide)
- [Thermal Receipt Printing](#-thermal-receipt-printing)
- [Project Structure](#-project-structure)
- [Database Structure](#-database-structure)
- [Runtime Data & Configuration](#-runtime-data--configuration)
- [Backup & Restore](#-backup--restore)
- [Customization & Development](#-customization--development)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)
- [Credits & Support](#-credits--support)

---

## 🚀 Introduction

**Open POS** is a complete point of sale application designed for small and medium
businesses — cafes, restaurants, bakeries, tuck shops and retail counters. It was
created by **Muhammad Sayban** under the **Saban Productions** brand to give shop
owners a powerful, **free and open-source** alternative to expensive POS software.

Everything runs **entirely on your own computer**. There is no cloud, no account,
no internet dependency and **no recurring fees**. All of your business data —
products, orders, staff, expenses and settings — is stored in a local SQLite
database that never leaves your device.

This project is released into the **public domain** — anyone can download the
source code, **change its name, use it, customize it and sell it** with no
restrictions whatsoever. See [LICENSE.txt](LICENSE.txt).

---

## ✨ Features

### 🏪 Store & Branding
- Customizable **store name, logo, email, phone, address and currency** (`Rs`, `$`, `€`, `£`, `AED`, `SAR`)
- Your store logo appears on the login screen, sidebar, and can be printed on receipts

### 🛒 Quick Sale (TakeAway & Delivery)
- Two dedicated tabs for **TakeAway** and **Delivery** orders
- Waiter & **Rider** assignment, customer name / phone / **delivery address**
- Configurable **delivery** and **takeaway** service charges
- Print **KOT** (Kitchen Order Ticket) and send the order to a pending queue
- Pending orders can be **edited, cancelled or marked completed**
- Completed order history with **print bill / print rider copy** options

### 🍽️ Dining (Table Management)
- Visual table grid with live status: **FREE / OCCUPIED / REQUEST BILL**
- Tap a table to open its order screen, assign a waiter, and start taking items
- Actions: **Print KOT**, **Request Bill**, **Final Bill & Close**, **Close Table**
- Table capacity (seats) and occupied/request-bill counters on the dashboard

### 🧾 Cart & Billing Engine
- Product search + category filter chips
- Per-item quantity controls, **per-item notes/instructions**, and order-level notes
- **Discounts** (flat amount or percentage), configurable **sales tax** per order type
- Auto-calculation of subtotal, discount, tax, service charges and total

### 📦 Products & Categories
- Full **product catalog** with category management
- Product **price and cost** (cost powers profit reports)
- Add, edit, delete, search and filter products

### 👥 Staff & Users (Role-based security)
- **Staff management**: waiters, captains, runners and riders
- **User accounts** with three roles — `admin`, `manager`, `cashier`
- Passwords are stored with **PBKDF2-SHA256 hashing + random salts** (never plain text)
- Role-based access control hides features that a role cannot use
- Enable / disable accounts, reset passwords, delete users

### 📊 Reports & Analytics
- **Dashboard**: today's sales, orders, items sold, busy tables + last-7-days chart
- **Sales report**: daily trend line chart, order-type pie chart, detailed table
- **Profit & Loss**: full statement (net sales → COGS → gross profit → expenses → net profit)
- **Products**: top-selling items, revenue by category
- **Staff performance**: waiter revenue and rider delivery analytics
- **Expenses**: by-category pie chart + detailed breakdown
- **Payments**: breakdown by payment method (Cash / Card / QR)
- Filters by **date preset, order type, payment method and waiter**
- **Export any report to CSV** in one click

### 💸 Expense Tracking
- Add expenses with category, description, amount and date
- Manage expense categories; monthly spending summary
- Expenses flow directly into the Profit & Loss report

### 🖨️ Thermal Receipt Printing (ESC/POS)
- Prints to any Windows thermal/receipt printer via the **win32print** API
- Choose a printer, **character encoding** (`cp437`, `cp850`, `utf-8`, `cp1252`) and **paper width** (42 = 80mm, 32 = 58mm)
- Print your **store logo** as a monochrome raster on receipts
- Receipt types: **KOT**, **Requested Bill**, **Rider Copy**, **Final Bill**, **Test Print**
- Automatic paper cut (configurable), auto-fit text wrapping, bold / double-size headings

### 💾 Backup, Restore & Safety
- **Manual backup** (download `.db` file) and **restore** from a backup file
- **Automatic daily backups** on app startup (kept in `data/backups/`)
- **Factory reset** ("Clear All Data") with `CLEAR` confirmation
- Backup validation (required tables + `PRAGMA integrity_check`) before restoring

### 🛡️ Reliability & Polish
- Modern, clean, light UI with a custom **Qt stylesheet (QSS)** theme
- Collapsible sidebar, **F11 fullscreen**, right-click **refresh** menu
- Global **crash guard** that logs unhandled exceptions to `data/logs/app.log`
- SQLite **WAL mode**, foreign keys, busy timeout and thread-safe access

---

## 🧰 Tech Stack & Libraries

| Library | Purpose |
| ------- | ------- |
| [**PySide6**](https://doc.qt.io/qtforpython/) (Qt for Python 6) | Complete GUI framework — windows, widgets, layouts, charts, styling |
| [**SQLite3**](https://docs.python.org/3/library/sqlite3.html) (stdlib) | Local embedded database — no server required |
| [**Pillow** (PIL)](https://python-pillow.org/) | Image handling — renders the store logo into thermal-printer raster bytes |
| [**pywin32**](https://pypi.org/project/pywin32/) | Native Windows printer API (`win32print`) — enumerate, open and write to printers |
| **Python stdlib** | `hashlib` (PBKDF2 password hashing), `logging`, `csv`, `threading`, `struct`, `pathlib`, `shutil`, `uuid`, `secrets`, `datetime` |

All chart widgets (`BarChart`, `LineChart`, `PieChart`, `HBarChart`) are **hand-drawn with Qt's QPainter** — no extra plotting library is needed.

---

## 📋 Requirements

- **Windows 10 / 11** (printer support uses the Windows printing API)
- **Python 3.10 or newer** ([python.org/downloads](https://www.python.org/downloads/))
- During installation, check **"Add Python to PATH"** (or use the `py` launcher)

> This is a **pure Python source project** — there is no bundled executable and no
> exe-building dependency in the repository. You run the source directly.

---

## 🔧 Installation

### 1. Get the code

```bash
git clone https://github.com/your-username/Open-POS.git
cd Open-POS
```

or download and extract the ZIP archive from GitHub.

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

The `requirements.txt` file contains:

```
PySide6>=6.5
Pillow>=10.0
pywin32>=306
```

> ⚠️ **Pillow is optional.** If it is missing, the app still works — it simply
> skips printing the logo on receipts. `pywin32` is needed for receipt printing.

### 4. Run the app

```bash
python main.py
```

---

## 🚀 Quick Start (First Run)

On first launch, Open POS automatically:

1. Creates the SQLite database at `data/openpos.db`
2. Builds all required tables and indexes
3. Seeds **demo data**: default categories, sample products, tables `T1`–`T8`,
   sample staff, and default settings

Log in with the default administrator account:

| Username | Password |
| -------- | -------- |
| `admin`  | `admin123` |

> 🔐 **Security tip:** immediately open **Settings → Users** and change the
> default admin password.

---

## 📖 Usage Guide

| Section | What you can do |
| ------- | --------------- |
| **Dashboard** | Today's sales, order count, items sold, busy tables, 7-day sales chart, recent orders |
| **Quick Sale** | TakeAway and Delivery orders — assign waiter/rider, add items, print KOT, manage pending/completed |
| **Dining** | Tap a table card to open its order; print KOT / request bill / final bill / close table |
| **Products** | Manage product catalog and categories (name, category, price, cost) |
| **Expenses** | Log daily spending, manage expense categories, see monthly total |
| **Reports** | Filter by date/type/payment/waiter across 6 tabs; export any view to CSV |
| **Settings** | Store profile & logo, tax & charges, tables, staff, users, printing, backup/restore |

---

## 🖨️ Thermal Receipt Printing

1. Connect a thermal/receipt printer to the PC (USB or network) and power it on.
2. Go to **Settings → Printing**.
3. Pick your printer (or **System Default**), choose the **encoding** and **paper width**:
   - `42` characters = 80mm thermal paper
   - `32` characters = 58mm thermal paper
4. Click **Print Test Receipt** to verify.
5. Optional: enable **"Show logo on receipt"** under *Tax Management → Receipt Customization*
   and upload your logo in *Settings → Store*.

Receipts are generated as raw **ESC/POS** byte streams (see `app/printing/`) and sent
directly to the printer. Supported receipts: KOT, Requested Bill, Rider Copy,
Final Bill, and Test Print.

---

## 📁 Project Structure

```
Open POS/
├── app/                              # Application package
│   ├── config.py                     # App constants, paths, data dirs
│   ├── database/
│   │   └── db.py                     # SQLite schema, migrations, seed data, backup/restore
│   ├── printing/
│   │   ├── escpos_builder.py         # ESC/POS byte builder + PNG → raster converter
│   │   └── printer_service.py        # Printer detection, raw printing, receipt templates
│   ├── services/                     # Business-logic layer (singleton services)
│   │   ├── auth_service.py           # Login/logout, user & password management
│   │   ├── expense_service.py        # Expense CRUD + category summaries
│   │   ├── order_service.py          # Order lifecycle, items, discount, tax, totals
│   │   ├── product_service.py        # Products & categories
│   │   ├── report_service.py         # Sales / P&L / ranking / staff analytics
│   │   ├── settings_service.py       # Key/value settings + order numbering
│   │   ├── staff_service.py          # Staff (waiters, riders, ...)
│   │   └── table_service.py          # Table CRUD + status tracking
│   ├── ui/                           # Qt user interface
│   │   ├── main_window.py            # Main window, sidebar, navigation
│   │   ├── login_view.py             # Login dialog
│   │   ├── dashboard_view.py         # Dashboard page
│   │   ├── pos_view.py               # Quick Sale (TakeAway / Delivery)
│   │   ├── dining_view.py            # Table grid
│   │   ├── table_popup.py            # Per-table order popup
│   │   ├── cart_panel.py             # Reusable product grid + cart widget
│   │   ├── products_view.py          # Product & category management
│   │   ├── expenses_view.py          # Expense tracking
│   │   ├── reports_view.py           # Reports with charts + CSV export
│   │   ├── settings_view.py          # All settings tabs
│   │   ├── charts.py                 # Custom QPainter charts (bar/line/pie/hbar)
│   │   ├── icons.py                  # Vector icons drawn with QPainter
│   │   ├── keys.py                   # Keyboard shortcut helpers
│   │   └── theme.py                  # Global Qt stylesheet (QSS)
│   └── utils/
│       ├── helpers.py                # Hashing, date/number formatting utilities
│       └── crash_guard.py            # Logging + unhandled-exception guard
├── data/                             # Runtime data (auto-created, gitignored)
│   ├── openpos.db                    # SQLite database
│   ├── logos/                        # Uploaded store logos
│   ├── backups/                      # Automatic daily backups
│   └── logs/                         # Application logs
├── main.py                           # Entry point
├── requirements.txt                  # Python dependencies
├── logo.ico                          # Application icon
├── LICENSE.txt                       # Public Domain license (no restrictions)
└── README.md                         # This file
```

---

## 🗄️ Database Structure

All data lives in a single **SQLite** file at `data/openpos.db` (WAL mode, foreign
keys enabled). The schema is created automatically on first run.

| Table | Purpose | Key columns |
| ----- | ------- | ----------- |
| `users` | System accounts | `username` (unique), `password_hash`, `salt`, `full_name`, `role` (`admin`/`manager`/`cashier`), `is_active` |
| `settings` | Key/value store | `key` (PK), `value` |
| `categories` | Product categories | `name` (unique), `sort_order` |
| `products` | Menu items | `category_id` (FK), `name`, `price`, `cost`, `is_active` |
| `tables` | Dining tables | `table_no` (unique), `seats`, `status` (`free`/`occupied`/`request_bill`), `current_order_id` |
| `staff` | Staff members | `name`, `role` (`Waiter`/`Captain`/`Runner`/`Rider`), `phone`, `is_active` |
| `orders` | Orders / bills | `order_number` (unique), `order_type` (`dine-in`/`takeaway`/`delivery`), `table_id`, `waiter_id`, `rider_id`, `cashier_id`, `status`, `subtotal`, `discount`, `discount_type`, `service_charge`, `tax`, `total`, `instructions`, `customer_name`/`phone`/`address`, `payment_method`, `closed_at` |
| `order_items` | Line items per order | `order_id` (FK, cascade), `product_id`, `name`, `price`, `qty`, `instructions` |
| `expense_categories` | Expense categories | `name` (unique) |
| `expenses` | Business expenses | `category_id` (FK), `category_name`, `description`, `amount`, `expense_date`, `created_by` |

Indexes: `idx_orders_created`, `idx_orders_status`, `idx_order_items_order`, `idx_expenses_date`.

A built-in **migration system** (`db.py::_migrate`) keeps older databases up to date
with minimal effort as the project evolves.

---

## 🗂️ Runtime Data & Configuration

| Item | Location |
| ---- | -------- |
| Database | `data/openpos.db` |
| Store logo files | `data/logos/` |
| Automatic backups | `data/backups/openpos_backup_*.db` |
| Logs | `data/logs/app.log` |

The `data/` folder is **automatically created** and is excluded from version
control (see `.gitignore`). Deleting it resets the app to factory defaults.

Application constants (name, version, paths) live in `app/config.py`.
Business settings are stored as key/value rows in the `settings` table and are
edited through **Settings → Store** and **Settings → Tax Management**.

---

## 💾 Backup & Restore

- **Automatic:** on every startup, if the last backup is older than 24 hours, a
  copy is written to `data/backups/`.
- **Manual:** *Settings → Backup / Restore → Download Backup* saves a `.db` file
  anywhere you choose.
- **Restore:** *Apply Backup File* validates the file (table presence + integrity
  check) and replaces the live database. You are signed out afterwards.
- **Factory reset:** *Clear All Data* deletes everything and re-seeds demo data
  (type `CLEAR` to confirm).

---

## 🔧 Customization & Development

Open POS is deliberately layered for easy modification:

- **Add a screen:** create a view in `app/ui/`, register it in `main_window.py::NAV`
  and update `ROLE_ACCESS` for permissions.
- **Change the look:** edit the global stylesheet in `app/ui/theme.py`.
- **Add a report:** extend `app/services/report_service.py` and wire it into
  `app/ui/reports_view.py`.
- **Change the data model:** edit `_SCHEMA` in `app/database/db.py` and add a
  migration in `_migrate()`.
- **Print formats:** tweak the receipt templates in
  `app/printing/printer_service.py` or the low-level ESC/POS builder in
  `app/printing/escpos_builder.py`.

Code style notes:
- The project targets **Python 3.10+** (uses `str | None` union syntax).
- Services are module-level singletons (`xxx_service`) bound to one database
  connection; rebinding is handled centrally in `db.py::rebind_services`.
- There are no external test frameworks configured; validate changes with a
  syntax check and a manual run:

```bash
python -m compileall app main.py
python main.py
```

---

## 🐛 Troubleshooting

| Problem | Solution |
| ------- | -------- |
| `No module named PySide6` | Dependencies not installed — run `pip install -r requirements.txt` |
| "No printer is available" | Connect & power on the receipt printer, then select it in *Settings → Printing* |
| Receipt prints with wrong characters | Change the **character encoding** (try `cp437`) or paper width in Settings |
| Logo does not print | Install Pillow (`pip install Pillow`) and enable *Show logo on receipt* |
| "Database is missing tables" | The DB file is corrupt or old — restore a backup from `data/backups/` |
| App won't start at all | Check `data/logs/app.log` for the detailed error stack trace |

---

## 📄 License

This project is released into the **public domain** — see [LICENSE.txt](LICENSE.txt).

There are **no restrictions of any kind**. You are free to:

- ✅ **Use** Open POS for any purpose, including commercial use
- ✅ **Modify** and **customize** the source code however you like
- ✅ **Change the name** and branding
- ✅ **Put your own name** on it and sell it
- ✅ **Distribute** copies and share it with others

Do whatever you want with it — free forever.

---

## 👨‍💻 Credits & Support

Open POS was designed and developed by **Muhammad Sayban** and is published under
the **Saban Productions** brand.

- **Author:** Muhammad Sayban
- **Brand:** Saban Productions
- **Email:** saban.productions00@gmail.com
- **License:** Public Domain (no restrictions)

If you find this project useful, consider starring ⭐ the repository. Bug reports,
feature ideas and pull requests are always welcome.

---

<div align="center">

**Open POS** — Free. Open Source. Yours.

© 2026 Muhammad Sayban | Saban Productions

</div>
"# OPEN-POS---Free-SmartPOS-Software." 
"# OPEN-POS---Free-SmartPOS-Software." 
