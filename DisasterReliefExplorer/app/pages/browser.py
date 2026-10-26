from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QVBoxLayout

from ..widgets import PageHeader, ResultTable, label
from .base import Page


class BrowserPage(Page):
    title = "Tables & Data"

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(12)
        lay.addWidget(PageHeader("Tables & Data", "Browse any table or view, just like FlameRobin's data grid."))
        bar = QHBoxLayout()
        self.combo = QComboBox()
        self.combo.setMinimumWidth(260)
        self.combo.currentTextChanged.connect(self.load)
        self.filter = QLineEdit()
        self.filter.setPlaceholderText("Filter rows...")
        self.filter.setClearButtonEnabled(True)
        self.filter.textChanged.connect(self.apply_filter)
        bar.addWidget(label("Table / view:"))
        bar.addWidget(self.combo)
        bar.addSpacing(12)
        bar.addWidget(self.filter, 1)
        lay.addLayout(bar)
        self.schema = label("", "muted", wrap=True)
        lay.addWidget(self.schema)
        self.grid = ResultTable()
        lay.addWidget(self.grid, 1)
        self.status = label("", "muted")
        lay.addWidget(self.status)

    def on_connected(self) -> None:
        self.combo.blockSignals(True)
        self.combo.clear()
        if self.db:
            names = self.db.tables()
            views = self.db.tables(views=True)
            self.combo.addItems(names + views)
        self.combo.blockSignals(False)
        self.load(self.combo.currentText())

    def load(self, name: str) -> None:
        if not self.db or not name:
            self.grid.clear()
            return
        try:
            cols = self.db.columns(name)
            pks = set(self.db.primary_keys(name))
            self.schema.setText("   ".join(
                f"{'* ' if c['name'] in pks else ''}{c['name']} {c['type']}" for c in cols))
            res = self.db.query(f'SELECT * FROM "{name}"')
            self.grid.set_result(res)
            self.apply_filter(self.filter.text(), total=len(res.rows), ms=res.elapsed_ms, trunc=res.truncated)
        except Exception as e:
            self.db.rollback()
            self.grid.clear()
            self.status.setText(f"Error: {self.err_text(e)}")

    def apply_filter(self, text: str, total: int | None = None, ms: float = 0, trunc: bool = False) -> None:
        shown = self.grid.filter_rows(text)
        n = self.grid.model().rowCount()
        extra = f" (first {n:,} rows only)" if trunc else ""
        self.status.setText(f"{shown:,} of {n:,} rows shown{extra}   |   * = primary key column")
