from __future__ import annotations

from PySide6.QtWidgets import QWidget

from ..db import Database


class Page(QWidget):
    """Every page gets the live Database and is refreshed whenever it is shown."""
    title = ""

    def __init__(self):
        super().__init__()
        self.setObjectName("page")
        self.db: Database | None = None

    def set_db(self, db: Database | None) -> None:
        self.db = db
        self.on_connected()

    def on_connected(self) -> None:  # override
        pass

    def refresh(self) -> None:       # override
        pass

    @staticmethod
    def err_text(exc: Exception) -> str:
        return " ".join(str(exc).split())
