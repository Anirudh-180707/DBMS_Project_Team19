"""Dark charcoal theme that mirrors the case-study slides and the FlameRobin grid."""
from PySide6.QtGui import QColor, QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

BG = "#2E2E2E"
PANEL = "#3A3A3A"
PANEL_ALT = "#444444"
HEADER = "#5C5C5C"
DEEP = "#232323"
BORDER = "#555555"
TEXT = "#F2F2F2"
MUTED = "#B0B0B0"
ACCENT = "#E0A458"
GREEN = "#7FB28E"
RED = "#D98080"

MONO_FAMILIES = ["Consolas", "Cascadia Mono", "DejaVu Sans Mono", "Menlo", "Courier New", "monospace"]
UI_FAMILIES = ["Segoe UI", "Calibri", "Helvetica Neue", "Arial", "sans-serif"]


def mono(size: int = 10, bold: bool = False) -> QFont:
    f = QFont()
    f.setFamilies(MONO_FAMILIES)
    f.setStyleHint(QFont.StyleHint.Monospace)
    f.setPointSize(size)
    f.setBold(bold)
    return f


def qcolor(hex_: str) -> QColor:
    return QColor(hex_)


QSS = f"""
* {{ font-family: "Segoe UI", "Calibri", "Helvetica Neue", Arial, sans-serif; font-size: 10pt; color: {TEXT}; }}
QMainWindow, QDialog, QWidget#page, QStackedWidget {{ background: {BG}; }}
QLabel {{ background: transparent; }}
QLabel[role="h1"] {{ font-family: "Consolas", "DejaVu Sans Mono", monospace; font-size: 19pt; font-weight: bold; }}
QLabel[role="h2"] {{ font-family: "Consolas", "DejaVu Sans Mono", monospace; font-size: 12pt; font-weight: bold; color: {ACCENT}; }}
QLabel[role="muted"] {{ color: {MUTED}; }}
QLabel[role="ok"] {{ color: {GREEN}; }}
QLabel[role="err"] {{ color: {RED}; }}
QFrame[role="card"] {{ background: {PANEL}; border-radius: 8px; }}
QFrame[role="deep"] {{ background: {DEEP}; border-radius: 8px; }}
QLabel[role="kpi"] {{ font-family: "Consolas", "DejaVu Sans Mono", monospace; font-size: 26pt; font-weight: bold; }}

QListWidget#nav {{ background: {DEEP}; border: none; outline: 0; padding: 8px 6px; }}
QListWidget#nav::item {{ padding: 10px 14px; border-radius: 6px; color: {MUTED}; }}
QListWidget#nav::item:hover {{ background: {PANEL}; color: {TEXT}; }}
QListWidget#nav::item:selected {{ background: {PANEL_ALT}; color: {ACCENT}; }}

QPushButton {{ background: {HEADER}; border: 1px solid {BORDER}; border-radius: 6px; padding: 7px 16px; }}
QPushButton:hover {{ background: #6B6B6B; }}
QPushButton:pressed {{ background: {PANEL_ALT}; }}
QPushButton:disabled {{ color: #888; background: {PANEL}; }}
QPushButton[role="primary"] {{ background: {ACCENT}; color: #1E1E1E; border: none; font-weight: bold; }}
QPushButton[role="primary"]:hover {{ background: #EBB46B; }}
QPushButton[role="danger"] {{ background: #7A4A4A; }}

QLineEdit, QSpinBox, QComboBox, QPlainTextEdit, QTextEdit {{
  background: {DEEP}; border: 1px solid {BORDER}; border-radius: 5px; padding: 5px 8px;
  selection-background-color: {ACCENT}; selection-color: #1E1E1E; }}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {{ border: 1px solid {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{ background: {DEEP}; selection-background-color: {HEADER}; border: 1px solid {BORDER}; }}
QPlainTextEdit[code="true"], QTextEdit[code="true"] {{ font-family: "Consolas", "DejaVu Sans Mono", monospace; }}
QCheckBox, QRadioButton {{ spacing: 8px; }}

QTableView {{ background: {PANEL}; alternate-background-color: {PANEL}; gridline-color: {BORDER};
  border: 1px solid {BORDER}; selection-background-color: #6E6E6E; selection-color: {TEXT};
  font-family: "Consolas", "DejaVu Sans Mono", monospace; font-size: 10pt; }}
QHeaderView::section {{ background: {HEADER}; color: {TEXT}; padding: 6px 8px; border: none;
  border-right: 1px solid {BORDER}; border-bottom: 1px solid {BORDER};
  font-family: "Consolas", "DejaVu Sans Mono", monospace; font-weight: bold; }}
QTableCornerButton::section {{ background: {HEADER}; border: none; }}

QListWidget {{ background: {PANEL}; border: 1px solid {BORDER}; outline: 0; padding: 4px; }}
QListWidget::item {{ padding: 8px 10px; border-radius: 5px; }}
QListWidget::item:hover {{ background: {PANEL_ALT}; }}
QListWidget::item:selected {{ background: {HEADER}; color: {ACCENT}; }}
QTableView QHeaderView {{ background: {BG}; }}
QHeaderView::section:vertical {{ background: {PANEL_ALT}; color: {MUTED}; padding: 0 6px; font-weight: normal;
  border: none; border-bottom: 1px solid {BORDER}; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid {MUTED}; border-radius: 3px; background: {DEEP}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border: 1px solid {ACCENT}; }}
QTreeWidget {{ background: {PANEL}; border: 1px solid {BORDER}; outline: 0; }}
QTreeWidget::item {{ padding: 4px 2px; }}
QTreeWidget::item:selected {{ background: {PANEL_ALT}; color: {ACCENT}; }}

QScrollBar:vertical {{ background: {BG}; width: 12px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {HEADER}; border-radius: 5px; min-height: 28px; }}
QScrollBar:horizontal {{ background: {BG}; height: 12px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: {HEADER}; border-radius: 5px; min-width: 28px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QSplitter::handle {{ background: {BG}; }}
QStatusBar {{ background: {DEEP}; color: {MUTED}; }}
QToolTip {{ background: {DEEP}; color: {TEXT}; border: 1px solid {BORDER}; padding: 4px; }}
QGraphicsView {{ background: {BG}; border: 1px solid {BORDER}; border-radius: 6px; }}
"""


def apply(app: QApplication) -> None:
    from PySide6.QtGui import QPalette
    app.setStyle("Fusion")
    pal = QPalette()
    for role, col in ((QPalette.Window, BG), (QPalette.WindowText, TEXT), (QPalette.Base, DEEP),
                      (QPalette.AlternateBase, PANEL), (QPalette.Text, TEXT), (QPalette.Button, HEADER),
                      (QPalette.ButtonText, TEXT), (QPalette.ToolTipBase, DEEP), (QPalette.ToolTipText, TEXT),
                      (QPalette.Highlight, ACCENT), (QPalette.HighlightedText, "#1E1E1E"),
                      (QPalette.PlaceholderText, "#8A8A8A")):
        pal.setColor(role, QColor(col))
    app.setPalette(pal)
    app.setStyleSheet(QSS)
