"""Reusable widgets: result grid, KPI tile, bar chart, SQL highlighter, page header."""
from __future__ import annotations

import re

from PySide6.QtCore import QRectF, QRegularExpression, Qt
from PySide6.QtGui import (QColor, QFont, QFontMetrics, QPainter, QStandardItem,
                           QStandardItemModel, QSyntaxHighlighter, QTextCharFormat)
from PySide6.QtWidgets import (QAbstractItemView, QFrame, QHeaderView, QLabel, QPlainTextEdit,
                               QSizePolicy, QTableView, QVBoxLayout, QWidget)

from . import theme
from .db import QueryResult, display

NUMERIC = (int, float)


def label(text: str = "", role: str = "", wrap: bool = False) -> QLabel:
    lb = QLabel(text)
    if role:
        lb.setProperty("role", role)
    lb.setWordWrap(wrap)
    return lb


def card(role: str = "card") -> QFrame:
    f = QFrame()
    f.setProperty("role", role)
    return f


class PageHeader(QWidget):
    def __init__(self, title: str, subtitle: str = ""):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        lay.addWidget(label(title, "h1"))
        if subtitle:
            lay.addWidget(label(subtitle, "muted", wrap=True))


class ResultTable(QTableView):
    """Read-only grid that looks like FlameRobin's data grid."""

    def __init__(self):
        super().__init__()
        self._model = QStandardItemModel(self)
        self.setModel(self._model)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.setShowGrid(True)
        self.setAlternatingRowColors(False)
        self.verticalHeader().setDefaultSectionSize(26)
        self.verticalHeader().setVisible(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setHighlightSections(False)
        self.setWordWrap(False)
        self.setSortingEnabled(False)

    def clear(self) -> None:
        self._model.clear()

    def set_result(self, res: QueryResult) -> None:
        m = self._model
        m.clear()
        m.setHorizontalHeaderLabels(res.columns)
        for row in res.rows:
            items = []
            for v in row:
                it = QStandardItem(display(v))
                if isinstance(v, NUMERIC) and not isinstance(v, bool):
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if v is None:
                    it.setForeground(QColor(theme.MUTED))
                it.setData(v if isinstance(v, (int, float, str)) else display(v), Qt.ItemDataRole.UserRole)
                items.append(it)
            m.appendRow(items)
        hh = self.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.resizeColumnsToContents()
        for i in range(m.columnCount()):
            w = min(max(self.columnWidth(i) + 18, 90), 380)
            self.setColumnWidth(i, w)
        hh.setStretchLastSection(True)

    def filter_rows(self, text: str) -> int:
        """Hide rows that do not contain *text* in any cell. Returns visible row count."""
        text = text.strip().lower()
        shown = 0
        for r in range(self._model.rowCount()):
            hit = not text or any(
                text in (self._model.item(r, c).text().lower())
                for c in range(self._model.columnCount()))
            self.setRowHidden(r, not hit)
            shown += hit
        return shown


class KpiTile(QFrame):
    def __init__(self, caption: str):
        super().__init__()
        self.setProperty("role", "card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(0)
        self.value = label("-", "kpi")
        self.value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cap = label(caption, "muted")
        cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.value)
        lay.addWidget(cap)

    def set_value(self, v, accent: bool = False) -> None:
        self.value.setText("-" if v is None else f"{v:,}" if isinstance(v, (int, float)) else str(v))
        self.value.setStyleSheet(f"color: {theme.ACCENT};" if accent else "")


class BarChart(QWidget):
    """Horizontal bar chart: label on the left, value at the end of each bar."""

    def __init__(self, title: str):
        super().__init__()
        self.title = title
        self.data: list[tuple[str, float]] = []
        self.setMinimumHeight(260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_data(self, data: list[tuple[str, float]]) -> None:
        self.data = data
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect())
        p.setBrush(QColor(theme.PANEL))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(r, 8, 8)
        tf = theme.mono(11, True)
        p.setFont(tf)
        p.setPen(QColor(theme.ACCENT))
        p.drawText(QRectF(16, 10, r.width() - 32, 24), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.title)
        if not self.data:
            p.setPen(QColor(theme.MUTED))
            p.setFont(QFont(self.font().family(), 10))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, "No data")
            return
        f = QFont(self.font().family(), 9)
        p.setFont(f)
        fm = QFontMetrics(f)
        top, bottom = 44, 12
        n = len(self.data)
        row_h = min(30.0, (r.height() - top - bottom) / n)
        lab_w = min(max(fm.horizontalAdvance(l) for l, _ in self.data) + 12, r.width() * 0.42)
        val_w = max(fm.horizontalAdvance(f"{v:,.0f}") for _, v in self.data) + 10
        x0 = 16 + lab_w
        bar_max = max(10.0, r.width() - x0 - val_w - 20)
        vmax = max(v for _, v in self.data) or 1
        for i, (lab, v) in enumerate(self.data):
            y = top + i * row_h
            p.setPen(QColor(theme.TEXT))
            p.drawText(QRectF(16, y, lab_w - 8, row_h), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                       fm.elidedText(lab, Qt.TextElideMode.ElideRight, int(lab_w - 8)))
            w = bar_max * (v / vmax)
            p.setBrush(QColor(theme.ACCENT))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(QRectF(x0, y + row_h * 0.18, max(w, 2), row_h * 0.64), 3, 3)
            p.setPen(QColor(theme.MUTED))
            p.drawText(QRectF(x0 + w + 6, y, val_w, row_h), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"{v:,.0f}")


SQL_KEYWORDS = (
    "SELECT FROM WHERE JOIN LEFT RIGHT INNER OUTER FULL ON GROUP BY ORDER HAVING AS AND OR NOT IN IS NULL "
    "INSERT INTO VALUES UPDATE SET DELETE CREATE ALTER DROP TABLE VIEW INDEX TRIGGER PROCEDURE EXCEPTION "
    "PRIMARY KEY FOREIGN REFERENCES CHECK DEFAULT UNIQUE BEGIN END IF THEN ELSE FOR DO DECLARE VARIABLE "
    "EXECUTE RETURNS RETURNING EXCEPTION BEFORE AFTER ACTIVE INACTIVE POSITION NEW OLD COUNT SUM AVG MIN MAX "
    "DISTINCT DESC ASC LIKE BETWEEN EXISTS CASE WHEN COALESCE SUSPEND STARTING WITH CONTAINING"
).split()


class SqlHighlighter(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc)

        def fmt(color, bold=False, italic=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(QFont.Weight.Bold)
            f.setFontItalic(italic)
            return f
        kw = "|".join(sorted(set(SQL_KEYWORDS), key=len, reverse=True))
        self.rules = [
            (QRegularExpression(rf"\b({kw})\b", QRegularExpression.PatternOption.CaseInsensitiveOption), fmt(theme.ACCENT, True)),
            (QRegularExpression(r"\b\d+(\.\d+)?\b"), fmt("#9CC7E8")),
            (QRegularExpression(r":[A-Za-z_][A-Za-z0-9_]*"), fmt("#C9A0DC")),
            (QRegularExpression(r"'[^']*'"), fmt(theme.GREEN)),
            (QRegularExpression(r"--[^\n]*"), fmt("#8A8A8A", italic=True)),
        ]

    def highlightBlock(self, text: str) -> None:
        for rx, f in self.rules:
            it = rx.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), f)


def code_view(read_only: bool = True, text: str = "") -> QPlainTextEdit:
    ed = QPlainTextEdit()
    ed.setProperty("code", True)
    ed.setFont(theme.mono(10))
    ed.setReadOnly(read_only)
    ed.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
    ed.setTabStopDistance(28)
    SqlHighlighter(ed.document())
    if text:
        ed.setPlainText(text)
    return ed


def first_keyword(sql: str) -> str:
    s = re.sub(r"(--[^\n]*\n|/\*.*?\*/)", " ", sql, flags=re.S).strip()
    m = re.match(r"[A-Za-z]+", s)
    return m.group(0).upper() if m else ""
