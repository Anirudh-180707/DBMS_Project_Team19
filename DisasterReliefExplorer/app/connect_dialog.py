from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (QDialog, QFileDialog, QFormLayout, QHBoxLayout, QLineEdit, QPushButton,
                               QSpinBox, QVBoxLayout, QWidget)

from .db import ConnectionSettings, Database
from .widgets import label


class ConnectDialog(QDialog):
    """Asks for the connection details and opens the database. Result in .database."""

    def __init__(self, parent=None, preset: ConnectionSettings | None = None):
        super().__init__(parent)
        self.setWindowTitle("Connect to Firebird")
        self.setMinimumWidth(560)
        self.database: Database | None = None
        qs = QSettings("DisasterReliefExplorer", "Connection")
        s = preset or ConnectionSettings(
            host=qs.value("host", ""), port=int(qs.value("port", 3050)), database=qs.value("database", ""),
            user=qs.value("user", "SYSDBA"), client_library=qs.value("client_library", ""))

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)
        lay.addWidget(label("Connect to your database", "h1"))
        lay.addWidget(label("Choose the .fdb file you created in FlameRobin. Leave Host empty to open the file "
                            "directly (embedded), or enter a host such as localhost to use a running Firebird server.",
                            "muted", wrap=True))
        form = QFormLayout()
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(14)
        self.host = QLineEdit(s.host)
        self.host.setPlaceholderText("empty = local file / embedded, or e.g. localhost")
        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(s.port)
        hp = QHBoxLayout()
        hp.addWidget(self.host, 1)
        hp.addWidget(label("Port"))
        hp.addWidget(self.port)
        hpw = QWidget()
        hpw.setLayout(hp)
        hp.setContentsMargins(0, 0, 0, 0)
        self.path = QLineEdit(s.database)
        self.path.setPlaceholderText(r"C:\data\RELIEF.FDB")
        b = QPushButton("Browse...")
        b.clicked.connect(self.browse_db)
        pr = QHBoxLayout()
        pr.addWidget(self.path, 1)
        pr.addWidget(b)
        prw = QWidget()
        prw.setLayout(pr)
        pr.setContentsMargins(0, 0, 0, 0)
        self.user = QLineEdit(s.user)
        self.pw = QLineEdit(s.password)
        self.pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.lib = QLineEdit(s.client_library)
        self.lib.setPlaceholderText("optional: path to fbclient.dll (needed if Firebird is not installed)")
        b2 = QPushButton("Browse...")
        b2.clicked.connect(self.browse_lib)
        lr = QHBoxLayout()
        lr.addWidget(self.lib, 1)
        lr.addWidget(b2)
        lrw = QWidget()
        lrw.setLayout(lr)
        lr.setContentsMargins(0, 0, 0, 0)
        form.addRow("Host", hpw)
        form.addRow("Database file", prw)
        form.addRow("User", self.user)
        form.addRow("Password", self.pw)
        form.addRow("Client library", lrw)
        lay.addLayout(form)
        self.msg = label("", "err", wrap=True)
        lay.addWidget(self.msg)
        row = QHBoxLayout()
        row.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self.ok = QPushButton("Connect")
        self.ok.setProperty("role", "primary")
        self.ok.setDefault(True)
        self.ok.clicked.connect(self.connect_now)
        row.addWidget(cancel)
        row.addWidget(self.ok)
        lay.addLayout(row)

    def browse_db(self) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "Select Firebird database", "", "Firebird databases (*.fdb *.FDB *.gdb);;All files (*)")
        if f:
            self.path.setText(f)

    def browse_lib(self) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "Select fbclient library", "", "Libraries (*.dll *.so *.dylib);;All files (*)")
        if f:
            self.lib.setText(f)

    def settings(self) -> ConnectionSettings:
        return ConnectionSettings(host=self.host.text(), port=self.port.value(), database=self.path.text().strip(),
                                  user=self.user.text().strip(), password=self.pw.text(),
                                  client_library=self.lib.text().strip())

    def connect_now(self) -> None:
        s = self.settings()
        if not s.database:
            self.msg.setText("Please choose a database file.")
            return
        self.ok.setEnabled(False)
        self.msg.setText("")
        try:
            self.database = Database(s)
        except Exception as e:
            self.msg.setText("Could not connect: " + " ".join(str(e).split()))
            self.ok.setEnabled(True)
            return
        qs = QSettings("DisasterReliefExplorer", "Connection")
        for k, v in (("host", s.host), ("port", s.port), ("database", s.database), ("user", s.user),
                     ("client_library", s.client_library)):
            qs.setValue(k, v)
        self.accept()
