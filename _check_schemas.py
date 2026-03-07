import sqlite3, os

# billing.db
bp = r"C:\Dme_Solutions\Data\billing.db"
print("billing.db exists:", os.path.exists(bp))
if os.path.exists(bp):
    conn = sqlite3.connect(bp)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("=== BILLING TABLES ===")
    tables = [r[0] for r in c.fetchall()]
    for t in tables:
        print(f"\n--- {t} ---")
        c.execute(f"PRAGMA table_info({t})")
        for r in c.fetchall():
            print(r)
    conn.close()

# inventory.db
ip = r"C:\Dme_Solutions\Data\inventory.db"
print("\ninventory.db exists:", os.path.exists(ip))
if os.path.exists(ip):
    conn = sqlite3.connect(ip)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("=== INVENTORY TABLES ===")
    tables = [r[0] for r in c.fetchall()]
    for t in tables:
        print(f"\n--- {t} ---")
        c.execute(f"PRAGMA table_info({t})")
        for r in c.fetchall():
            print(r)
    conn.close()

# order_items
conn = sqlite3.connect(r"C:\Dme_Solutions\Data\orders.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("\n=== ORDERS DB TABLES ===")
tables = [r[0] for r in c.fetchall()]
for t in tables:
    print(t)
print("\n=== ORDER_ITEMS COLUMNS ===")
c.execute("PRAGMA table_info(order_items)")
for r in c.fetchall():
    print(r)
conn.close()
