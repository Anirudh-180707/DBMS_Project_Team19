from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout

from ..widgets import PageHeader, code_view, label
from .base import Page


class ObjectsPage(Page):
    title = "Database Objects"

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(12)
        lay.addWidget(PageHeader("Database Objects",
                                 "Views, indexes, the stored procedure and the trigger, with their source read from the system tables."))
        split = QSplitter(Qt.Orientation.Horizontal)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setMaximumWidth(320)
        self.tree.currentItemChanged.connect(self.show_item)
        split.addWidget(self.tree)
        self.src = code_view(True)
        split.addWidget(self.src)
        split.setStretchFactor(1, 1)
        lay.addWidget(split, 1)
        self.meta = label("", "muted", wrap=True)
        lay.addWidget(self.meta)

    def on_connected(self) -> None:
        self.tree.clear()
        self.src.clear()
        if not self.db:
            return
        db = self.db
        try:
            groups = {
                "Triggers": [(n, f"-- TRIGGER {n} ON {t}\n{s}", f"Fires on table {t}") for n, t, s in db.triggers()],
                "Stored procedures": [(n, f"-- PROCEDURE {n}\n{s}", "Run with EXECUTE PROCEDURE") for n, s in db.procedures()],
                "Views": [(n, f"CREATE VIEW {n} AS\n{s}", "A saved query; stores no data of its own") for n, s in db.view_sources()],
                "Indexes": [(n, f"CREATE INDEX {n} ON {t} ({c});", f"Speeds up lookups on {t}") for n, t, c in db.indexes()],
            }
        except Exception as e:
            db.rollback()
            self.meta.setText(f"Could not read metadata: {self.err_text(e)}")
            return
        first = None
        for g, items in groups.items():
            top = QTreeWidgetItem([f"{g} ({len(items)})"])
            top.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.tree.addTopLevelItem(top)
            for name, source, note in items:
                it = QTreeWidgetItem([name])
                it.setData(0, Qt.ItemDataRole.UserRole, (source, note))
                top.addChild(it)
                first = first or it
            top.setExpanded(True)
        if first:
            self.tree.setCurrentItem(first)

    def show_item(self, cur, _prev) -> None:
        d = cur.data(0, Qt.ItemDataRole.UserRole) if cur else None
        if d:
            self.src.setPlainText(d[0].strip())
            self.meta.setText(d[1])
