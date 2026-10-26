"""Thin wrapper around firebird-driver so the UI never touches the driver directly."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from firebird.driver import connect, driver_config
from firebird.driver import DatabaseError  # noqa: F401  (re-exported for the UI)


@dataclass
class ConnectionSettings:
    host: str = ""            # blank = embedded / local file access
    port: int = 3050
    database: str = ""
    user: str = "SYSDBA"
    password: str = ""
    charset: str = "UTF8"
    client_library: str = ""  # optional path to fbclient.dll / libfbclient.so

    def dsn(self) -> str:
        if self.host.strip():
            return f"{self.host.strip()}/{self.port}:{self.database}"
        return self.database


@dataclass
class QueryResult:
    columns: list[str] = field(default_factory=list)
    rows: list[tuple] = field(default_factory=list)
    elapsed_ms: float = 0.0
    truncated: bool = False
    affected: int = -1


def display(value) -> str:
    """Format a value for display in a grid."""
    if value is None:
        return "NULL"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, Decimal):
        return f"{value:f}"
    if isinstance(value, bytes):
        return value.hex()
    if hasattr(value, "read"):          # BLOB
        try:
            v = value.read()
            return v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v)
        except Exception:
            return "<blob>"
    return str(value)


class Database:
    MAX_ROWS = 2000

    def __init__(self, settings: ConnectionSettings):
        self.settings = settings
        if settings.client_library.strip():
            driver_config.fb_client_library.value = settings.client_library.strip()
        self.con = connect(
            settings.dsn(),
            user=settings.user or None,
            password=settings.password or None,
            charset=settings.charset or "UTF8",
        )

    # ---- helpers -------------------------------------------------------
    def close(self) -> None:
        try:
            self.con.close()
        except Exception:
            pass

    def info(self) -> dict:
        i = self.con.info
        return {
            "server_version": getattr(i, "version", ""),
            "engine": getattr(i, "engine_version", ""),
            "page_size": getattr(i, "page_size", ""),
            "dialect": getattr(i, "sql_dialect", ""),
            "database": self.settings.dsn(),
        }

    def query(self, sql: str, params: tuple = (), *, commit: bool = True,
              limit: int | None = None) -> QueryResult:
        """Run a statement that returns rows (or not) and return everything."""
        limit = self.MAX_ROWS if limit is None else limit
        t0 = time.perf_counter()
        cur = self.con.cursor()
        try:
            cur.execute(sql, params)
            res = QueryResult()
            if cur.description:
                res.columns = [d[0] for d in cur.description]
                rows = cur.fetchmany(limit + 1)
                if len(rows) > limit:
                    res.truncated = True
                    rows = rows[:limit]
                res.rows = [tuple(r) for r in rows]
            res.affected = cur.affected_rows if not cur.description else len(res.rows)
        finally:
            cur.close()
        if commit:
            self.con.commit()
        res.elapsed_ms = (time.perf_counter() - t0) * 1000
        return res

    def scalar(self, sql: str, params: tuple = (), default=None, *, commit: bool = True):
        """First column of the first row. Pass commit=False to read inside an open transaction."""
        try:
            r = self.query(sql, params, limit=1, commit=commit)
            return r.rows[0][0] if r.rows else default
        except Exception:
            self.rollback()
            return default

    def execute(self, sql: str, params: tuple = (), *, commit: bool = False) -> None:
        cur = self.con.cursor()
        try:
            cur.execute(sql, params)
        finally:
            cur.close()
        if commit:
            self.con.commit()

    def commit(self) -> None:
        self.con.commit()

    def rollback(self) -> None:
        try:
            self.con.rollback()
        except Exception:
            pass

    # ---- metadata ------------------------------------------------------
    def tables(self, views: bool = False) -> list[str]:
        kind = "IS NOT NULL" if views else "IS NULL"
        r = self.query(
            "SELECT TRIM(RDB$RELATION_NAME) FROM RDB$RELATIONS "
            f"WHERE COALESCE(RDB$SYSTEM_FLAG,0)=0 AND RDB$VIEW_BLR {kind} "
            "ORDER BY 1")
        return [x[0] for x in r.rows]

    def columns(self, table: str) -> list[dict]:
        r = self.query(
            "SELECT TRIM(rf.RDB$FIELD_NAME), f.RDB$FIELD_TYPE, f.RDB$FIELD_SUB_TYPE, "
            "f.RDB$CHARACTER_LENGTH, f.RDB$FIELD_PRECISION, f.RDB$FIELD_SCALE, "
            "COALESCE(rf.RDB$NULL_FLAG,0) "
            "FROM RDB$RELATION_FIELDS rf JOIN RDB$FIELDS f ON f.RDB$FIELD_NAME = rf.RDB$FIELD_SOURCE "
            "WHERE rf.RDB$RELATION_NAME = ? ORDER BY rf.RDB$FIELD_POSITION", (table,))
        names = {7: "SMALLINT", 8: "INTEGER", 10: "FLOAT", 12: "DATE", 13: "TIME",
                 14: "CHAR", 16: "BIGINT", 23: "BOOLEAN", 27: "DOUBLE", 35: "TIMESTAMP",
                 37: "VARCHAR", 261: "BLOB"}
        out = []
        for name, ft, sub, clen, prec, scale, nn in r.rows:
            t = names.get(ft, str(ft))
            if ft in (14, 37) and clen:
                t = f"{t}({clen})"
            if ft in (7, 8, 16) and sub in (1, 2) and prec:
                t = f"{'NUMERIC' if sub == 1 else 'DECIMAL'}({prec},{-scale})"
            out.append({"name": name, "type": t, "not_null": bool(nn)})
        return out

    def primary_keys(self, table: str) -> list[str]:
        r = self.query(
            "SELECT TRIM(s.RDB$FIELD_NAME) FROM RDB$RELATION_CONSTRAINTS rc "
            "JOIN RDB$INDEX_SEGMENTS s ON s.RDB$INDEX_NAME = rc.RDB$INDEX_NAME "
            "WHERE rc.RDB$CONSTRAINT_TYPE='PRIMARY KEY' AND rc.RDB$RELATION_NAME = ? "
            "ORDER BY s.RDB$FIELD_POSITION", (table,))
        return [x[0] for x in r.rows]

    def foreign_keys(self) -> list[dict]:
        """Return [{table, column, ref_table, ref_column}] for every FK."""
        r = self.query(
            "SELECT TRIM(rc.RDB$RELATION_NAME), TRIM(s.RDB$FIELD_NAME), "
            "TRIM(rc2.RDB$RELATION_NAME), TRIM(s2.RDB$FIELD_NAME) "
            "FROM RDB$RELATION_CONSTRAINTS rc "
            "JOIN RDB$REF_CONSTRAINTS refc ON refc.RDB$CONSTRAINT_NAME = rc.RDB$CONSTRAINT_NAME "
            "JOIN RDB$RELATION_CONSTRAINTS rc2 ON rc2.RDB$CONSTRAINT_NAME = refc.RDB$CONST_NAME_UQ "
            "JOIN RDB$INDEX_SEGMENTS s ON s.RDB$INDEX_NAME = rc.RDB$INDEX_NAME "
            "JOIN RDB$INDEX_SEGMENTS s2 ON s2.RDB$INDEX_NAME = rc2.RDB$INDEX_NAME "
            "AND s2.RDB$FIELD_POSITION = s.RDB$FIELD_POSITION "
            "WHERE rc.RDB$CONSTRAINT_TYPE='FOREIGN KEY'")
        return [dict(table=a, column=b, ref_table=c, ref_column=d) for a, b, c, d in r.rows]

    def triggers(self) -> list[tuple[str, str, str]]:
        r = self.query(
            "SELECT TRIM(RDB$TRIGGER_NAME), TRIM(RDB$RELATION_NAME), RDB$TRIGGER_SOURCE "
            "FROM RDB$TRIGGERS WHERE COALESCE(RDB$SYSTEM_FLAG,0)=0 ORDER BY 1")
        return [(a, b or "", display(c)) for a, b, c in r.rows]

    def procedures(self) -> list[tuple[str, str]]:
        r = self.query(
            "SELECT TRIM(RDB$PROCEDURE_NAME), RDB$PROCEDURE_SOURCE FROM RDB$PROCEDURES "
            "WHERE COALESCE(RDB$SYSTEM_FLAG,0)=0 ORDER BY 1")
        return [(a, display(b)) for a, b in r.rows]

    def view_sources(self) -> list[tuple[str, str]]:
        r = self.query(
            "SELECT TRIM(RDB$RELATION_NAME), RDB$VIEW_SOURCE FROM RDB$RELATIONS "
            "WHERE COALESCE(RDB$SYSTEM_FLAG,0)=0 AND RDB$VIEW_BLR IS NOT NULL ORDER BY 1")
        return [(a, display(b)) for a, b in r.rows]

    def indexes(self) -> list[tuple[str, str, str]]:
        r = self.query(
            "SELECT TRIM(i.RDB$INDEX_NAME), TRIM(i.RDB$RELATION_NAME), "
            "(SELECT LIST(TRIM(s.RDB$FIELD_NAME), ', ') FROM RDB$INDEX_SEGMENTS s "
            " WHERE s.RDB$INDEX_NAME = i.RDB$INDEX_NAME) "
            "FROM RDB$INDICES i WHERE COALESCE(i.RDB$SYSTEM_FLAG,0)=0 "
            "AND i.RDB$INDEX_NAME NOT STARTING WITH 'RDB$' ORDER BY 2, 1")
        return [(a, b, c or "") for a, b, c in r.rows]
