# Disaster Relief Database Explorer

A Windows-friendly desktop app (Python + PySide6) that showcases the Firebird disaster-relief case study:
live dashboard, table browser, the three reports and views, a **trigger demo**, a **stored-procedure demo**,
an ER diagram generated from the database itself, the source of every trigger/procedure/view/index,
and a SQL console. Dark charcoal theme to match the slides.

## Run it

1. Install Python 3.10+ (64-bit) from python.org, tick "Add python.exe to PATH".
2. Double-click `install_deps.bat` (or: `pip install -r requirements.txt`).
3. Double-click `run_app.bat` (or: `python main.py`).
4. In the connection window enter:
   * **Host**: `localhost` if you use the Firebird server that FlameRobin connects to. Leave empty to open the .fdb file directly (embedded).
   * **Database file**: full path to your .fdb, as shown in FlameRobin (Database > Registration info).
   * **User / Password**: usually `SYSDBA` and the password you set during install.
   * **Client library**: leave empty if Firebird is installed. Otherwise browse to `fbclient.dll` (must be 64-bit to match Python).

Shortcut: `python main.py --db C:\data\RELIEF.FDB --host localhost --user SYSDBA --password yourpass`

## Pages

| Page | What it shows |
|---|---|
| Dashboard | KPI tiles + bar charts (requests per disaster, stock per resource) |
| Tables & Data | Any table or view in a FlameRobin-style grid, with filter |
| Queries & Views | Queries A, B, C from the slides and the 3 views; SQL shown, one click to run |
| Trigger Demo | Inserts a DELIVERY_ITEM; shows INVENTORY before/after, or the trigger's rejection (qty 0, not enough stock) |
| Procedure Demo | Runs UPDATE_REQUEST_STATUS and verifies it; invalid status shows the CHECK constraint |
| ER Diagram | Built from system tables (PK/FK, 1 / M). Ctrl + wheel to zoom |
| Database Objects | Source of triggers, procedures, views and indexes |
| SQL Console | One statement at a time; read-only unless you tick "Allow data changes" |

The two demos **roll back by default**, so your data stays exactly as it was. Untick the box to make a change permanent.

## No database handy?

`python tools/make_sample_db.py C:\temp\relief.fdb --host localhost --password yourpass` creates a fresh database with the
case-study schema, views, indexes, procedure, trigger and the fictional sample rows.

## Build an .exe (optional)

Double-click `build_exe.bat`. Output: `dist\ReliefDBExplorer\ReliefDBExplorer.exe`.

## Notes

* The app expects the case-study table and column names (DISASTER, RELIEF_REQUEST, INVENTORY, DELIVERY_ITEM, ...). Panels whose
  tables are missing show "-" instead of crashing.
* Tested here against Firebird 5.0 with firebird-driver. Firebird 3 and 4 also work with this driver.
