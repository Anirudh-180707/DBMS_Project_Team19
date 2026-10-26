"""Live demos of the two programmable objects in the case study: the trigger and the stored procedure."""
from __future__ import annotations

from html import escape

from PySide6.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QPushButton, QSpinBox,
                               QTextEdit, QVBoxLayout)

from .. import theme
from ..widgets import PageHeader, card, code_view, label
from .base import Page


class LogBox(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setProperty("code", True)
        self.setFont(theme.mono(10))

    def add(self, text: str, color: str = theme.TEXT) -> None:
        self.append(f'<span style="color:{color}">{escape(text)}</span>')


def clean_error(exc: Exception) -> str:
    """Keep the useful part of a Firebird error message."""
    return " ".join(str(exc).split())


class TriggerDemoPage(Page):
    title = "Trigger Demo"

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(12)
        lay.addWidget(PageHeader(
            "Trigger demo: BI_DELIVERY_ITEM_STOCK",
            "Insert a delivery item and watch the trigger deduct stock from INVENTORY, or reject the insert."))

        form = card()
        g = QGridLayout(form)
        g.setContentsMargins(16, 14, 16, 14)
        g.setHorizontalSpacing(14)
        g.setVerticalSpacing(10)
        self.delivery = QComboBox()
        self.resource = QComboBox()
        self.qty = QSpinBox()
        self.qty.setRange(-1000, 10_000_000)
        self.qty.setValue(10)
        self.rollback = QCheckBox("Roll back afterwards (leave the data unchanged)")
        self.rollback.setChecked(True)
        g.addWidget(label("Delivery"), 0, 0)
        g.addWidget(self.delivery, 0, 1)
        g.addWidget(label("Resource"), 0, 2)
        g.addWidget(self.resource, 0, 3)
        g.addWidget(label("Quantity"), 0, 4)
        g.addWidget(self.qty, 0, 5)
        g.addWidget(self.rollback, 1, 0, 1, 4)
        row = QHBoxLayout()
        self.b_valid = QPushButton("Insert (valid)")
        self.b_valid.setProperty("role", "primary")
        self.b_zero = QPushButton("Try quantity 0")
        self.b_big = QPushButton("Try more than in stock")
        for b in (self.b_valid, self.b_zero, self.b_big):
            row.addWidget(b)
        row.addStretch(1)
        g.addLayout(row, 1, 4, 1, 2)
        g.setColumnStretch(1, 2)
        g.setColumnStretch(3, 2)
        lay.addWidget(form)

        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.s_before = self._stat("Stock before")
        self.s_after = self._stat("Stock after")
        self.s_change = self._stat("Change")
        for w in (self.s_before, self.s_after, self.s_change):
            stats.addWidget(w[0])
        lay.addLayout(stats)

        self.sql = code_view(True)
        self.sql.setMaximumHeight(90)
        lay.addWidget(self.sql)
        self.log = LogBox()
        self.log.setPlaceholderText("Results appear here. Try 'Insert (valid)' first, then the two rejection cases.")
        lay.addWidget(self.log, 1)

        self.delivery.currentIndexChanged.connect(self._fill_resources)
        self.b_valid.clicked.connect(lambda: self.run(self.qty.value()))
        self.b_zero.clicked.connect(lambda: self.run(0))
        self.b_big.clicked.connect(lambda: self.run(None))

    @staticmethod
    def _stat(caption: str):
        c = card()
        l = QVBoxLayout(c)
        l.setContentsMargins(14, 10, 14, 10)
        l.setSpacing(0)
        v = label("-", "kpi")
        l.addWidget(v)
        l.addWidget(label(caption, "muted"))
        return c, v

    def on_connected(self) -> None:
        self.delivery.blockSignals(True)
        self.delivery.clear()
        self.log.clear()
        if not self.db:
            return
        try:
            r = self.db.query(
                "SELECT D.DELIVERY_ID, D.WAREHOUSE_ID, W.WAREHOUSE_NAME, D.DELIVERY_STATUS "
                "FROM DELIVERY D JOIN WAREHOUSE W ON W.WAREHOUSE_ID = D.WAREHOUSE_ID ORDER BY 1")
            for did, wid, wname, st in r.rows:
                self.delivery.addItem(f"#{did}  {wname}  ({st})", (did, wid))
            self.delivery.blockSignals(False)
            self._fill_resources()
        except Exception as e:
            self.db.rollback()
            self.delivery.blockSignals(False)
            self.log.add(f"Could not load deliveries: {clean_error(e)}", theme.RED)

    def _fill_resources(self) -> None:
        self.resource.clear()
        data = self.delivery.currentData()
        if not (self.db and data):
            return
        did, wid = data
        r = self.db.query(
            "SELECT R.RESOURCE_ID, R.RESOURCE_NAME, COALESCE(I.QUANTITY, -1), "
            "(SELECT COUNT(*) FROM DELIVERY_ITEM X WHERE X.DELIVERY_ID = ? AND X.RESOURCE_ID = R.RESOURCE_ID) "
            "FROM RESOURCE R LEFT JOIN INVENTORY I ON I.RESOURCE_ID = R.RESOURCE_ID AND I.WAREHOUSE_ID = ? "
            "ORDER BY 4, R.RESOURCE_ID", (did, wid))
        for rid, name, qty, used in r.rows:
            note = "no stock row" if qty < 0 else f"stock {qty:,}"
            if used:
                note += ", already in this delivery"
            self.resource.addItem(f"{name}  ({note})", rid)

    def _stock(self, wid: int, rid: int):
        return self.db.scalar(
            "SELECT QUANTITY FROM INVENTORY WHERE WAREHOUSE_ID = ? AND RESOURCE_ID = ?", (wid, rid), default=None)

    def run(self, qty) -> None:
        data = self.delivery.currentData()
        rid = self.resource.currentData()
        if not (self.db and data and rid is not None):
            return
        did, wid = data
        db = self.db
        before = self._stock(wid, rid)
        db.rollback()
        if qty is None:                      # "more than in stock"
            qty = (before or 0) + 1
        sql = f"INSERT INTO DELIVERY_ITEM (DELIVERY_ID, RESOURCE_ID, QUANTITY)\nVALUES ({did}, {rid}, {qty});"
        self.sql.setPlainText(sql)
        self.s_before[1].setText("-" if before is None else f"{before:,}")
        self.log.add(f"> {sql.replace(chr(10), ' ')}", theme.MUTED)
        try:
            db.execute("INSERT INTO DELIVERY_ITEM (DELIVERY_ID, RESOURCE_ID, QUANTITY) VALUES (?, ?, ?)",
                       (did, rid, qty))
            after = db.scalar("SELECT QUANTITY FROM INVENTORY WHERE WAREHOUSE_ID = ? AND RESOURCE_ID = ?",
                              (wid, rid), commit=False)
            self.s_after[1].setText("-" if after is None else f"{after:,}")
            delta = None if before is None or after is None else after - before
            self.s_change[1].setText("-" if delta is None else f"{delta:+,}")
            self.log.add(f"Insert accepted. The trigger changed stock {before} -> {after}.", theme.GREEN)
            if self.rollback.isChecked():
                db.rollback()
                self.log.add("Rolled back: database left unchanged.", theme.MUTED)
            else:
                db.commit()
                self.log.add("Committed: the change is now permanent.", theme.ACCENT)
        except Exception as e:
            db.rollback()
            self.s_after[1].setText(self.s_before[1].text())
            self.s_change[1].setText("0")
            self.log.add(f"Rejected by the database: {clean_error(e)}", theme.RED)
        self._fill_resources_keep()

    def _fill_resources_keep(self) -> None:
        idx = self.resource.currentIndex()
        self._fill_resources()
        self.resource.setCurrentIndex(max(idx, 0))


class ProcedureDemoPage(Page):
    title = "Procedure Demo"
    STATUSES = ["OPEN", "APPROVED", "FULFILLED", "CANCELLED"]

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(12)
        lay.addWidget(PageHeader(
            "Stored procedure demo: UPDATE_REQUEST_STATUS",
            "Call the procedure on a relief request and verify the result with a SELECT."))
        form = card()
        g = QGridLayout(form)
        g.setContentsMargins(16, 14, 16, 14)
        g.setHorizontalSpacing(14)
        g.setVerticalSpacing(10)
        self.request = QComboBox()
        self.status = QComboBox()
        self.status.addItems(self.STATUSES)
        self.status.setCurrentText("APPROVED")
        self.revert = QCheckBox("Roll back afterwards (leave the data unchanged)")
        self.revert.setChecked(True)
        g.addWidget(label("Request"), 0, 0)
        g.addWidget(self.request, 0, 1)
        g.addWidget(label("New status"), 0, 2)
        g.addWidget(self.status, 0, 3)
        g.addWidget(self.revert, 1, 0, 1, 2)
        row = QHBoxLayout()
        self.b_run = QPushButton("Execute procedure")
        self.b_run.setProperty("role", "primary")
        self.b_bad = QPushButton("Try invalid status 'DONE'")
        row.addWidget(self.b_run)
        row.addWidget(self.b_bad)
        row.addStretch(1)
        g.addLayout(row, 1, 2, 1, 2)
        g.setColumnStretch(1, 3)
        g.setColumnStretch(3, 1)
        lay.addWidget(form)

        stats = QHBoxLayout()
        stats.setSpacing(12)
        self.s_before = TriggerDemoPage._stat("Status before")
        self.s_after = TriggerDemoPage._stat("Status after")
        stats.addWidget(self.s_before[0])
        stats.addWidget(self.s_after[0])
        lay.addLayout(stats)
        self.sql = code_view(True)
        self.sql.setMaximumHeight(110)
        lay.addWidget(self.sql)
        self.log = LogBox()
        self.log.setPlaceholderText("Results appear here. Run the procedure, then try the invalid status to see the CHECK constraint react.")
        lay.addWidget(self.log, 1)
        self.b_run.clicked.connect(lambda: self.run(self.status.currentText()))
        self.b_bad.clicked.connect(lambda: self.run("DONE"))

    def on_connected(self) -> None:
        self.request.clear()
        self.log.clear()
        if not self.db:
            return
        try:
            r = self.db.query("SELECT REQUEST_ID, REQUESTED_BY, REQUEST_STATUS FROM RELIEF_REQUEST ORDER BY 1")
            for rid, by, st in r.rows:
                self.request.addItem(f"#{rid}  {by}  ({st})", rid)
        except Exception as e:
            self.db.rollback()
            self.log.add(f"Could not load requests: {clean_error(e)}", theme.RED)

    def _status(self, rid, commit: bool = True):
        return self.db.scalar("SELECT REQUEST_STATUS FROM RELIEF_REQUEST WHERE REQUEST_ID = ?", (rid,),
                              commit=commit)

    def run(self, new_status: str) -> None:
        rid = self.request.currentData()
        if not (self.db and rid is not None):
            return
        db = self.db
        before = self._status(rid)
        db.rollback()
        sql = (f"-- 1. Call the procedure\nEXECUTE PROCEDURE UPDATE_REQUEST_STATUS({rid}, '{new_status}');\n\n"
               f"-- 2. Verify the result\nSELECT REQUEST_ID, REQUEST_STATUS FROM RELIEF_REQUEST WHERE REQUEST_ID = {rid};")
        self.sql.setPlainText(sql)
        self.s_before[1].setText(str(before))
        self.log.add(f"> EXECUTE PROCEDURE UPDATE_REQUEST_STATUS({rid}, '{new_status}')", theme.MUTED)
        try:
            db.execute("EXECUTE PROCEDURE UPDATE_REQUEST_STATUS(?, ?)", (rid, new_status))
            after = self._status(rid, commit=False)
            self.s_after[1].setText(str(after))
            self.log.add(f"Procedure ran. REQUEST_STATUS is now {after}.", theme.GREEN)
            if self.revert.isChecked():
                db.rollback()
                self.log.add("Rolled back: database left unchanged.", theme.MUTED)
            else:
                db.commit()
                self.log.add("Committed: the change is now permanent.", theme.ACCENT)
                self.on_connected_keep(rid)
        except Exception as e:
            db.rollback()
            self.s_after[1].setText(str(before))
            self.log.add(f"Rejected by the database: {clean_error(e)}", theme.RED)

    def on_connected_keep(self, rid) -> None:
        log = self.log.toHtml()
        self.on_connected()
        self.log.setHtml(log)
        i = self.request.findData(rid)
        if i >= 0:
            self.request.setCurrentIndex(i)
