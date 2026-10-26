from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QSplitter, QVBoxLayout, QWidget

from ..widgets import PageHeader, ResultTable, code_view, label
from .base import Page

REPORTS = [
    ("A. Requests by disaster",
     "LEFT JOIN keeps disasters with zero requests. COUNT tallies requests, GROUP BY gives one row per disaster, ORDER BY lists the busiest first.",
     "SELECT D.DISASTER_NAME,\n  COUNT(RR.REQUEST_ID)\n    AS TOTAL_REQUESTS\nFROM DISASTER D\nLEFT JOIN RELIEF_REQUEST RR\n  ON D.DISASTER_ID =\n     RR.DISASTER_ID\nGROUP BY D.DISASTER_ID,\n         D.DISASTER_NAME\nORDER BY TOTAL_REQUESTS DESC"),
    ("B. Total stock by resource",
     "JOIN matches each resource with its stock rows. SUM adds quantities across warehouses; GROUP BY gives one total per resource.",
     "SELECT R.RESOURCE_NAME,\n  SUM(I.QUANTITY)\n    AS TOTAL_STOCK\nFROM RESOURCE R\nJOIN INVENTORY I\n  ON R.RESOURCE_ID =\n     I.RESOURCE_ID\nGROUP BY R.RESOURCE_ID,\n         R.RESOURCE_NAME\nORDER BY TOTAL_STOCK DESC"),
    ("C. Critical pending requests",
     "Querying the view filters open or approved requests to the most urgent ones, supporting prioritization.",
     "SELECT REQUEST_ID,\n  DISASTER_NAME,\n  REQUESTED_BY,\n  RESOURCE_NAME,\n  QUANTITY_NEEDED,\n  PRIORITY,\n  REQUEST_STATUS\nFROM V_PENDING_REQUESTS\nWHERE PRIORITY = 'CRITICAL'"),
    ("View: V_PENDING_REQUESTS", "Relief requests that are OPEN or APPROVED, joined with disaster and resource details.",
     "SELECT * FROM V_PENDING_REQUESTS"),
    ("View: V_INVENTORY_SUMMARY", "Warehouse, resource and inventory combined into one stock report.",
     "SELECT * FROM V_INVENTORY_SUMMARY"),
    ("View: V_DELIVERY_SUMMARY", "Deliveries with their requests, organizations, warehouses, items and resources.",
     "SELECT * FROM V_DELIVERY_SUMMARY"),
]


class ReportsPage(Page):
    title = "Queries & Views"

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(12)
        lay.addWidget(PageHeader("Queries & Views", "The reporting queries and saved views from the case study. Pick one and run it."))
        split = QSplitter(Qt.Orientation.Horizontal)
        self.list = QListWidget()
        self.list.setMaximumWidth(280)
        for name, _, _ in REPORTS:
            self.list.addItem(QListWidgetItem(name))
        self.list.currentRowChanged.connect(self.pick)
        split.addWidget(self.list)
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 0, 0, 0)
        rl.setSpacing(10)
        self.explain = label("", "muted", wrap=True)
        rl.addWidget(self.explain)
        self.sql = code_view(True)
        self.sql.setMaximumHeight(210)
        rl.addWidget(self.sql)
        row = QHBoxLayout()
        self.run_btn = QPushButton("Run query")
        self.run_btn.setProperty("role", "primary")
        self.run_btn.clicked.connect(self.run)
        self.status = label("", "muted")
        row.addWidget(self.run_btn)
        row.addWidget(self.status, 1)
        rl.addLayout(row)
        self.grid = ResultTable()
        rl.addWidget(self.grid, 1)
        split.addWidget(right)
        split.setStretchFactor(1, 1)
        lay.addWidget(split, 1)
        self.list.setCurrentRow(0)

    def pick(self, row: int) -> None:
        if row < 0:
            return
        _, why, sql = REPORTS[row]
        self.explain.setText(why)
        self.sql.setPlainText(sql)
        self.grid.clear()
        self.status.setText("")

    def run(self) -> None:
        if not self.db:
            return
        try:
            res = self.db.query(self.sql.toPlainText())
            self.grid.set_result(res)
            self.status.setText(f"{len(res.rows):,} rows in {res.elapsed_ms:.1f} ms")
        except Exception as e:
            self.db.rollback()
            self.grid.clear()
            self.status.setText(f"Error: {self.err_text(e)}")
