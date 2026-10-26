from __future__ import annotations

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout

from ..widgets import BarChart, KpiTile, PageHeader, label
from .base import Page

KPIS = [
    ("Disasters tracked", "SELECT COUNT(*) FROM DISASTER", False),
    ("Open requests", "SELECT COUNT(*) FROM RELIEF_REQUEST WHERE REQUEST_STATUS = 'OPEN'", False),
    ("Critical & pending", "SELECT COUNT(*) FROM RELIEF_REQUEST WHERE PRIORITY = 'CRITICAL' "
                           "AND REQUEST_STATUS IN ('OPEN','APPROVED')", True),
    ("Units in stock", "SELECT COALESCE(SUM(QUANTITY),0) FROM INVENTORY", False),
    ("Deliveries", "SELECT COUNT(*) FROM DELIVERY", False),
]

REQ_BY_DISASTER = (
    "SELECT D.DISASTER_NAME, COUNT(RR.REQUEST_ID) AS TOTAL_REQUESTS "
    "FROM DISASTER D LEFT JOIN RELIEF_REQUEST RR ON D.DISASTER_ID = RR.DISASTER_ID "
    "GROUP BY D.DISASTER_ID, D.DISASTER_NAME ORDER BY TOTAL_REQUESTS DESC")
STOCK_BY_RESOURCE = (
    "SELECT R.RESOURCE_NAME, SUM(I.QUANTITY) AS TOTAL_STOCK FROM RESOURCE R "
    "JOIN INVENTORY I ON R.RESOURCE_ID = I.RESOURCE_ID "
    "GROUP BY R.RESOURCE_ID, R.RESOURCE_NAME ORDER BY TOTAL_STOCK DESC")


class DashboardPage(Page):
    title = "Dashboard"

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(16)
        lay.addWidget(PageHeader("Dashboard", "Live numbers read straight from the Firebird database."))
        row = QHBoxLayout()
        row.setSpacing(12)
        self.tiles = []
        for cap, _, _ in KPIS:
            t = KpiTile(cap)
            self.tiles.append(t)
            row.addWidget(t)
        lay.addLayout(row)
        grid = QGridLayout()
        grid.setSpacing(12)
        self.chart_req = BarChart("Relief requests per disaster")
        self.chart_stock = BarChart("Total stock per resource")
        grid.addWidget(self.chart_req, 0, 0)
        grid.addWidget(self.chart_stock, 0, 1)
        lay.addLayout(grid, 1)
        self.note = label("", "muted")
        lay.addWidget(self.note)

    def refresh(self) -> None:
        if not self.db:
            return
        for tile, (_, sql, accent) in zip(self.tiles, KPIS):
            v = self.db.scalar(sql)
            tile.set_value(v if v is None else int(v), accent and bool(v))
        for chart, sql in ((self.chart_req, REQ_BY_DISASTER), (self.chart_stock, STOCK_BY_RESOURCE)):
            try:
                chart.set_data([(r[0], float(r[1] or 0)) for r in self.db.query(sql).rows])
            except Exception as e:  # missing table etc.
                self.db.rollback()
                chart.set_data([])
                self.note.setText(f"Some panels could not load: {self.err_text(e)}")
                return
        self.note.setText("")
