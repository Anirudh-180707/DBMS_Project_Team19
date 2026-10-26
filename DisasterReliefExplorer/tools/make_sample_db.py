"""Create a fresh Firebird database with the case-study schema and fictional sample data.

Usage:  python tools/make_sample_db.py  path/to/relief.fdb  [--user SYSDBA --password masterkey]
                                         [--host localhost] [--client-lib path/to/fbclient]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sample_data as S  # noqa: E402
from firebird.driver import create_database, driver_config  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("database")
    ap.add_argument("--host", default="")
    ap.add_argument("--user", default="SYSDBA")
    ap.add_argument("--password", default="masterkey")
    ap.add_argument("--client-lib", default="")
    a = ap.parse_args()
    if a.client_lib:
        driver_config.fb_client_library.value = a.client_lib
    dsn = f"{a.host}:{a.database}" if a.host else a.database
    con = create_database(dsn, user=a.user, password=a.password, charset="UTF8", overwrite=True)
    cur = con.cursor()
    for stmt in S.DDL:
        cur.execute(stmt)
    con.commit()

    def many(sql, rows):
        for r in rows:
            cur.execute(sql, r)
        con.commit()

    many("INSERT INTO DISASTER VALUES (?,?,?,?,?,?)", [
        (i, n, t, l, __import__("datetime").date.fromisoformat(d), s) for i, n, t, l, d, s in S.DISASTERS])
    many("INSERT INTO RESOURCE VALUES (?,?,?,?)", S.RESOURCES)
    many("INSERT INTO ORGANIZATION VALUES (?,?,?,?,?)", S.ORGS)
    many("INSERT INTO WAREHOUSE VALUES (?,?,?,?)", S.WAREHOUSES)
    many("INSERT INTO INVENTORY VALUES (?,?,?)", S.INVENTORY)
    many("INSERT INTO RELIEF_REQUEST (REQUEST_ID, DISASTER_ID, REQUESTED_BY, LOCATION, RESOURCE_ID,"
         " QUANTITY_NEEDED, PRIORITY, REQUEST_STATUS) VALUES (?,?,?,?,?,?,?,?)",
         [(r[0], r[7], r[1], r[2], r[3], r[4], r[5], r[6]) for r in S.REQUESTS])
    import datetime
    many("INSERT INTO DELIVERY VALUES (?,?,?,?,?,?)",
         [(a_, b, c, d, datetime.date.fromisoformat(e), f) for a_, b, c, d, e, f in S.DELIVERIES])
    many("INSERT INTO DELIVERY_ITEM VALUES (?,?,?)", S.DELIVERY_ITEMS)   # fires the stock trigger
    con.close()
    print("Created", a.database)


if __name__ == "__main__":
    main()
