from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QListWidget, QListWidgetItem, QMainWindow, QPushButton, QStackedWidget,
                               QVBoxLayout, QWidget)

from . import __version__
from .connect_dialog import ConnectDialog
from .db import Database
from .pages.browser import BrowserPage
from .pages.console import ConsolePage
from .pages.dashboard import DashboardPage
from .pages.demos import ProcedureDemoPage, TriggerDemoPage
from .pages.er_diagram import ErDiagramPage
from .pages.objects import ObjectsPage
from .pages.reports import ReportsPage
from .widgets import label


class MainWindow(QMainWindow):
    def __init__(self, db: Database | None = None):
        super().__init__()
        self.setWindowTitle("Disaster Relief Database Explorer  -  Firebird")
        self.resize(1280, 800)
        self.db: Database | None = None

        root = QWidget()
        root.setObjectName("page")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        side = QWidget()
        side.setFixedWidth(230)
        side.setStyleSheet("background:#232323;")
        sl = QVBoxLayout(side)
        sl.setContentsMargins(0, 18, 0, 12)
        brand = label("Relief DB", "h2")
        brand.setContentsMargins(18, 0, 0, 0)
        sub = label("Firebird case study", "muted")
        sub.setContentsMargins(18, 0, 0, 8)
        sl.addWidget(brand)
        sl.addWidget(sub)
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        sl.addWidget(self.nav, 1)
        self.conn_label = label("Not connected", "muted", wrap=True)
        self.conn_label.setContentsMargins(18, 0, 12, 0)
        sl.addWidget(self.conn_label)
        btn = QPushButton("Connection...")
        btn.clicked.connect(self.change_connection)
        btn.setStyleSheet("margin: 8px 14px 0 14px;")
        sl.addWidget(btn)
        outer.addWidget(side)

        self.stack = QStackedWidget()
        outer.addWidget(self.stack, 1)
        self.pages = [DashboardPage(), BrowserPage(), ReportsPage(), TriggerDemoPage(), ProcedureDemoPage(),
                      ErDiagramPage(), ObjectsPage(), ConsolePage()]
        for p in self.pages:
            self.stack.addWidget(p)
            it = QListWidgetItem(p.title)
            it.setSizeHint(it.sizeHint().expandedTo(it.sizeHint()))
            self.nav.addItem(it)
        self.nav.currentRowChanged.connect(self.show_page)
        self.statusBar().showMessage(f"Disaster Relief Database Explorer {__version__}")
        if db:
            self.attach(db)
        self.nav.setCurrentRow(0)

    def show_page(self, i: int) -> None:
        if i < 0:
            return
        self.stack.setCurrentIndex(i)
        self.pages[i].refresh()

    def attach(self, db: Database) -> None:
        if self.db:
            self.db.close()
        self.db = db
        for p in self.pages:
            p.set_db(db)
        i = db.info()
        self.conn_label.setText(f"Connected\nFirebird {i['server_version']}\n{i['database']}")
        self.conn_label.setProperty("role", "ok")
        self.conn_label.style().unpolish(self.conn_label)
        self.conn_label.style().polish(self.conn_label)
        self.pages[self.stack.currentIndex()].refresh()

    def change_connection(self) -> None:
        dlg = ConnectDialog(self)
        if dlg.exec() and dlg.database:
            self.attach(dlg.database)

    def closeEvent(self, e) -> None:
        if self.db:
            self.db.close()
        super().closeEvent(e)
