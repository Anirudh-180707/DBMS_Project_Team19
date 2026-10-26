"""ER diagram drawn from the live system tables (tables, columns, primary and foreign keys)."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QGraphicsPathItem, QGraphicsRectItem, QGraphicsScene, QGraphicsSimpleTextItem,
                               QGraphicsView, QHBoxLayout, QPushButton, QVBoxLayout)

from .. import theme
from ..widgets import PageHeader, label
from .base import Page

# (column, row) positions that mirror the layout of the case-study ER slide
KNOWN_LAYOUT = {
    "DISASTER": (0, 0), "RELIEF_REQUEST": (1, 0), "DELIVERY": (2, 0), "ORGANIZATION": (3, 0),
    "INVENTORY": (0, 1), "RESOURCE": (1, 1), "DELIVERY_ITEM": (2, 1), "WAREHOUSE": (3, 1),
}
ROW_H = 20
HEAD_H = 28
PAD = 10
GAP_X = 70
GAP_Y = 60


class ErView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, e):
        if e.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.scale(1.15 if e.angleDelta().y() > 0 else 1 / 1.15, 1.15 if e.angleDelta().y() > 0 else 1 / 1.15)
        else:
            super().wheelEvent(e)


class ErDiagramPage(Page):
    title = "ER Diagram"

    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 20)
        lay.setSpacing(12)
        lay.addWidget(PageHeader("Entity-Relationship Diagram",
                                 "Generated from the database's own metadata. Ctrl + mouse wheel zooms, drag to pan."))
        bar = QHBoxLayout()
        fit = QPushButton("Fit to window")
        fit.clicked.connect(self.fit)
        bar.addWidget(fit)
        bar.addWidget(label("PK = primary key    FK = foreign key    1 / M = one-to-many (1 = parent side, M = child side)", "muted"))
        bar.addStretch(1)
        lay.addLayout(bar)
        self.scene = QGraphicsScene(self)
        self.view = ErView(self.scene)
        lay.addWidget(self.view, 1)

    def showEvent(self, e):
        super().showEvent(e)
        self.fit()

    def fit(self) -> None:
        if self.scene.items():
            self.view.fitInView(self.scene.itemsBoundingRect().adjusted(-20, -20, 20, 20), Qt.AspectRatioMode.KeepAspectRatio)

    def on_connected(self) -> None:
        self.scene.clear()
        if not self.db:
            return
        db = self.db
        try:
            tables = db.tables()
            fks = db.foreign_keys()
            info = {}
            fk_cols = {}
            for f in fks:
                fk_cols.setdefault(f["table"], set()).add(f["column"])
            for t in tables:
                info[t] = (db.columns(t), set(db.primary_keys(t)))
        except Exception as e:
            db.rollback()
            t = self.scene.addSimpleText(f"Could not read metadata: {self.err_text(e)}")
            t.setBrush(QBrush(QColor(theme.RED)))
            return

        font = theme.mono(9)
        bold = theme.mono(10, True)
        fm, fmb = QFontMetrics(font), QFontMetrics(bold)
        sizes = {}
        for t, (cols, _) in info.items():
            w = fmb.horizontalAdvance(t) + 2 * PAD
            for c in cols:
                w = max(w, fm.horizontalAdvance(f"PK, FK  {c['name']}  {c['type']}") + 2 * PAD)
            sizes[t] = (w, HEAD_H + len(cols) * ROW_H + 8)

        pos = {}
        extra_row = 2
        extra_col = 0
        for t in tables:
            if t in KNOWN_LAYOUT:
                pos[t] = KNOWN_LAYOUT[t]
            else:
                pos[t] = (extra_col, extra_row)
                extra_col += 1
                if extra_col > 3:
                    extra_col, extra_row = 0, extra_row + 1
        ncols = max(c for c, _ in pos.values()) + 1 if pos else 0
        nrows = max(r for _, r in pos.values()) + 1 if pos else 0
        col_w = [max([sizes[t][0] for t in pos if pos[t][0] == c] or [0]) for c in range(ncols)]
        row_h = [max([sizes[t][1] for t in pos if pos[t][1] == r] or [0]) for r in range(nrows)]
        col_x = [sum(col_w[:c]) + GAP_X * c for c in range(ncols)]
        row_y = [sum(row_h[:r]) + GAP_Y * r for r in range(nrows)]
        rects = {}
        for t, (c, r) in pos.items():
            w, h = sizes[t]
            rects[t] = QRectF(col_x[c], row_y[r], w, h)

        # relationships first so boxes are drawn over them
        pen = QPen(QColor(theme.MUTED), 1.4)
        seen = set()
        bottom_routes = {}
        for f in fks:
            child, parent = f["table"], f["ref_table"]
            if child not in rects or parent not in rects or (child, parent, f["column"]) in seen:
                continue
            seen.add((child, parent, f["column"]))
            self._edge(rects, pos, child, parent, pen, bottom_routes, col_w, row_h, nrows)

        for t, rect in rects.items():
            cols, pks = info[t]
            self._box(t, rect, cols, pks, fk_cols.get(t, set()), font, bold)
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-30, -30, 30, 30))
        self.fit()

    def _box(self, name, rect, cols, pks, fks, font, bold):
        body = QGraphicsRectItem(rect)
        body.setBrush(QBrush(QColor(theme.PANEL)))
        body.setPen(QPen(QColor("#6A6A6A"), 1))
        body.setZValue(2)
        self.scene.addItem(body)
        head = QGraphicsRectItem(QRectF(rect.x(), rect.y(), rect.width(), HEAD_H))
        head.setBrush(QBrush(QColor(theme.HEADER)))
        head.setPen(QPen(Qt.PenStyle.NoPen))
        head.setZValue(3)
        self.scene.addItem(head)
        t = QGraphicsSimpleTextItem(name)
        t.setFont(bold)
        t.setBrush(QBrush(QColor(theme.TEXT)))
        t.setPos(rect.x() + (rect.width() - QFontMetrics(bold).horizontalAdvance(name)) / 2, rect.y() + 4)
        t.setZValue(4)
        self.scene.addItem(t)
        y = rect.y() + HEAD_H + 4
        for c in cols:
            tags = []
            if c["name"] in pks:
                tags.append("PK")
            if c["name"] in fks:
                tags.append("FK")
            tag = ", ".join(tags)
            if tag:
                ti = QGraphicsSimpleTextItem(tag)
                ti.setFont(font)
                ti.setBrush(QBrush(QColor(theme.ACCENT)))
                ti.setPos(rect.x() + PAD, y)
                ti.setZValue(4)
                self.scene.addItem(ti)
            tw = QFontMetrics(font).horizontalAdvance("PK, FK  ")
            ni = QGraphicsSimpleTextItem(c["name"])
            ni.setFont(font)
            ni.setBrush(QBrush(QColor(theme.TEXT)))
            ni.setPos(rect.x() + PAD + tw, y)
            ni.setZValue(4)
            self.scene.addItem(ni)
            ty = QGraphicsSimpleTextItem(c["type"])
            ty.setFont(font)
            ty.setBrush(QBrush(QColor(theme.MUTED)))
            ty.setPos(rect.right() - PAD - QFontMetrics(font).horizontalAdvance(c["type"]), y)
            ty.setZValue(4)
            self.scene.addItem(ty)
            y += ROW_H

    def _edge(self, rects, pos, child, parent, pen, bottom_routes, col_w, row_h, nrows):
        a, b = rects[child], rects[parent]
        (cc, cr), (pc, pr) = pos[child], pos[parent]
        pts: list[QPointF]
        if child == parent:
            return
        if cr == pr and abs(cc - pc) > 1:                     # same row, not adjacent: route underneath
            k = bottom_routes.get(cr, 0)
            bottom_routes[cr] = k + 1
            y = max(a.bottom(), b.bottom(), max(r.bottom() for t, r in rects.items() if pos[t][1] == cr)) + 18 + 12 * k
            pts = [QPointF(a.center().x(), a.bottom()), QPointF(a.center().x(), y),
                   QPointF(b.center().x(), y), QPointF(b.center().x(), b.bottom())]
            c_pt, p_pt = pts[0], pts[-1]
        elif cc == pc:                                         # vertical neighbours
            up = a.top() > b.top()
            p1 = QPointF(a.center().x(), a.top() if up else a.bottom())
            p2 = QPointF(b.center().x(), b.bottom() if up else b.top())
            pts = [p1, p2]
            c_pt, p_pt = p1, p2
        else:                                                  # horizontal neighbours with an elbow in the gap
            right = b.center().x() > a.center().x()
            x1 = a.right() if right else a.left()
            x2 = b.left() if right else b.right()
            xm = (x1 + x2) / 2
            y1 = a.top() + HEAD_H / 2
            y2 = b.top() + HEAD_H / 2
            if cr != pr:
                y1, y2 = a.center().y() if a.height() < b.height() else a.top() + a.height() / 2, b.top() + HEAD_H / 2
            pts = [QPointF(x1, y1), QPointF(xm, y1), QPointF(xm, y2), QPointF(x2, y2)]
            c_pt, p_pt = pts[0], pts[-1]
        path = QPainterPath(pts[0])
        for p in pts[1:]:
            path.lineTo(p)
        item = QGraphicsPathItem(path)
        item.setPen(pen)
        item.setZValue(1)
        self.scene.addItem(item)
        for pt, txt, other in ((c_pt, "M", pts[1]), (p_pt, "1", pts[-2])):
            t = QGraphicsSimpleTextItem(txt)
            t.setFont(theme.mono(9, True))
            t.setBrush(QBrush(QColor(theme.ACCENT)))
            dx = 6 if other.x() > pt.x() else -14 if other.x() < pt.x() else 6
            dy = 4 if other.y() > pt.y() else -18 if other.y() < pt.y() else -18
            t.setPos(pt.x() + dx if other.x() != pt.x() else pt.x() + 6, pt.y() + dy if other.y() != pt.y() else pt.y() - 18)
            t.setZValue(5)
            self.scene.addItem(t)
