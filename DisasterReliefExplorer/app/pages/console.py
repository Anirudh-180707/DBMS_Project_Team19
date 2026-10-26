from __future__ import annotations

from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QPushButton, QSplitter, QVBoxLayout
from PySide6.QtCore import Qt

from ..widgets import PageHeader, ResultTable, code_view, first_keyword, label
from .base import Page

READ_ONLY_OK = {"SELECT", "WITH", "VALUES"}


class ConsolePage(Page):
    title = "SQL Console"

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(12)
        lay.addWidget(PageHeader("SQL Console", "Type one SQL statement and press Run (F5 or Ctrl+Enter)."))
        split = QSplitter(Qt.Orientation.Vertical)
        self.editor = code_view(False, "SELECT * FROM DISASTER ORDER BY SEVERITY, DISASTER_NAME")
        split.addWidget(self.editor)
        self.grid = ResultTable()
        split.addWidget(self.grid)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 2)
        lay.addWidget(split, 1)
        row = QHBoxLayout()
        self.run_btn = QPushButton("Run")
        self.run_btn.setProperty("role", "primary")
        self.run_btn.clicked.connect(self.run)
        self.allow = QCheckBox("Allow data changes (INSERT / UPDATE / DELETE / DDL)")
        self.status = label("", "muted")
        row.addWidget(self.run_btn)
        row.addWidget(self.allow)
        row.addWidget(self.status, 1)
        lay.addLayout(row)
        for seq in ("F5", "Ctrl+Return"):
            QShortcut(QKeySequence(seq), self, activated=self.run)

    def run(self) -> None:
        if not self.db:
            return
        sql = self.editor.toPlainText().strip().rstrip(";").strip()
        if not sql:
            return
        kw = first_keyword(sql)
        if kw not in READ_ONLY_OK and not self.allow.isChecked():
            self.status.setProperty("role", "err")
            self.status.setText(f"{kw or 'This statement'} changes data. Tick 'Allow data changes' to run it.")
            self.status.style().unpolish(self.status)
            self.status.style().polish(self.status)
            return
        try:
            res = self.db.query(sql, commit=False)
            self.grid.set_result(res)
            if res.columns:
                msg = f"{len(res.rows):,} rows in {res.elapsed_ms:.1f} ms" + (" (first 2,000 shown)" if res.truncated else "")
            else:
                msg = f"OK in {res.elapsed_ms:.1f} ms"
            if kw in READ_ONLY_OK:
                self.db.rollback()
            else:
                self.db.commit()
                msg += "  - committed"
            role = "ok"
        except Exception as e:
            self.db.rollback()
            self.grid.clear()
            msg, role = f"Error: {self.err_text(e)}", "err"
        self.status.setProperty("role", role)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.status.setText(msg)
