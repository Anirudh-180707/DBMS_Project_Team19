"""Disaster Relief Database Explorer - run with:  python main.py
Optional quick start:  python main.py --db C:\\data\\RELIEF.FDB --user SYSDBA --password masterkey
"""
import argparse
import sys

from PySide6.QtWidgets import QApplication

from app import theme
from app.connect_dialog import ConnectDialog
from app.db import ConnectionSettings, Database
from app.mainwindow import MainWindow


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db")
    ap.add_argument("--host", default="")
    ap.add_argument("--port", type=int, default=3050)
    ap.add_argument("--user", default="SYSDBA")
    ap.add_argument("--password", default="")
    ap.add_argument("--client-lib", default="")
    args, qt_args = ap.parse_known_args()

    app = QApplication([sys.argv[0]] + qt_args)
    app.setApplicationName("Disaster Relief Database Explorer")
    theme.apply(app)

    db = None
    if args.db:
        try:
            db = Database(ConnectionSettings(host=args.host, port=args.port, database=args.db, user=args.user,
                                             password=args.password, client_library=args.client_lib))
        except Exception as e:
            print("Could not connect:", e, file=sys.stderr)
    if db is None:
        dlg = ConnectDialog()
        if not dlg.exec() or not dlg.database:
            return 0
        db = dlg.database
    win = MainWindow(db)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
