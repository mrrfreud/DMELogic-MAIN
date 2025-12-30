import datetime
import os
import sqlite3
import argparse
from typing import Iterable


def iter_candidate_dbs() -> Iterable[str]:
    # Common known locations (add more if needed)
    candidates = [
        r"C:\\Dme_Solutions\\Data\\orders.db",
        r"C:\\ProgramData\\DMELogic\\Data\\orders.db",
        r"C:\\FaxManagerData\\Data\\orders.db",
    ]
    # Also include possible backups alongside the primary DB
    for base in [r"C:\\Dme_Solutions\\Data", r"C:\\ProgramData\\DMELogic\\Data", r"C:\\FaxManagerData\\Data"]:
        if os.path.isdir(base):
            for name in os.listdir(base):
                if name.lower().startswith("orders") and ".db" in name.lower():
                    candidates.append(os.path.join(base, name))

    # De-dupe while preserving order
    seen: set[str] = set()
    for p in candidates:
        if p not in seen:
            seen.add(p)
            yield p


def probe_db(path: str) -> None:
    print(f"\nDB: {path}")
    if not os.path.exists(path):
        print("  missing")
        return

    st = os.stat(path)
    print(
        f"  size={st.st_size}  mtime={datetime.datetime.fromtimestamp(st.st_mtime)}"
    )

    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        print(f"  tables={len(tables)}  has_orders={'orders' in tables}")

        if "orders" in tables:
            cur.execute("SELECT COUNT(*) FROM orders")
            print(f"  orders_rows={cur.fetchone()[0]}")
        else:
            # Some older DBs used different table names; list the closest matches
            near = [t for t in tables if "order" in t.lower()]
            if near:
                print(f"  order-ish tables: {near[:20]}")

        conn.close()
    except Exception as e:
        print(f"  ERROR probing DB: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Probe candidate DMELogic orders.db files")
    parser.add_argument(
        "--paths",
        nargs="*",
        help="Optional explicit DB file paths to probe. If omitted, probes common known locations.",
    )
    args = parser.parse_args()

    paths = args.paths if args.paths else list(iter_candidate_dbs())
    for p in paths:
        probe_db(p)
